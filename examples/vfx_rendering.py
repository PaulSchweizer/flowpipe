"""Demo a complex workflow of a rendering with a series of subsequent actions:

- Render a CG render out of Maya
- Check the resulting images for potential defects caused by potential server glitches
- Register the CG render in the database
- Create and render a slap comp
- Convert the rendered slapcomp to a quicktime

+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   Rendering                                                                                                                    |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| +-----Rendering-----+          +--------Rendering---------+          +-------Rendering--------+           +------Rendering-------+           +--------Rendering--------+          +-------Rendering-------+          +--------default--------+ |
| |   CreateCamera    |          |   MayaSceneGeneration    |          |   HoudiniRender0-10    |           |   CheckImages0-10    |           |     CreateSlapComp      |          |    NukeRender0-10     |          |       Quicktime       | |
| |-------------------|          |--------------------------|          |------------------------|           |----------------------|           |-------------------------|          |-----------------------|          |-----------------------| |
| |     camera_file<> o--------->o camera_file<>            |          o frames<range(0...>     |      +--->o images<>             |           % images<>                |          o frames<range(0...>    |          % images<>              | |
| +-------------------+          |             scene_file<> o--------->o scene_file<>           |      |    |             images<> o---------->o  images.0<>             |     +--->o scene_file<>          |     +--->o  images.0<>           | |
|                                +--------------------------+     |    |           renderings<> o------+    +----------------------+      |--->o  images.10<>            |     |    |          renderings<> o-----+--->o  images.10<>          | |
|                                                                 |    +------------------------+           +-------Rendering-------+     +--->o  images.20<>            |     |    +-----------------------+     +--->o  images.20<>          | |
|                                                                 |    +--------Rendering--------+          |   CheckImages10-20    |     |    o template<nuke_te...>    |     |    +-------Rendering-------+     |    |           quicktime<> o |
|                                                                 |    |   HoudiniRender10-20    |          |-----------------------|     |    |              slapcomp<> o-----+    |    NukeRender10-20    |     |    +-----------------------+ |
|                                                                 |    |-------------------------|     +--->o images<>              |     |    +-------------------------+     |    |-----------------------|     |                              |
|                                                                 |    o frames<range(1...>      |     |    |              images<> o-----|    +-------Rendering-------+       |    o frames<range(1...>    |     |                              |
|                                                                 +--->o scene_file<>            |     |    +-----------------------+     |    |    UpdateDatabase     |       +--->o scene_file<>          |     |                              |
|                                                                 |    |            renderings<> o-----+    +-------Rendering-------+     |    |-----------------------|       |    |          renderings<> o-----|                              |
|                                                                 |    +-------------------------+          |   CheckImages20-30    |     |    o id_<123456>           |       |    +-----------------------+     |                              |
|                                                                 |    +--------Rendering--------+          |-----------------------|     |    % images<>              |       |    +-------Rendering-------+     |                              |
|                                                                 |    |   HoudiniRender20-30    |     +--->o images<>              |     |--->o  images.0<>           |       |    |    NukeRender20-30    |     |                              |
|                                                                 |    |-------------------------|     |    |              images<> o-----+--->o  images.10<>          |       |    |-----------------------|     |                              |
|                                                                 |    o frames<range(2...>      |     |    +-----------------------+     +--->o  images.20<>          |       |    o frames<range(2...>    |     |                              |
|                                                                 +--->o scene_file<>            |     |                                       |              status<> o       +--->o scene_file<>          |     |                              |
|                                                                      |            renderings<> o-----+                                       +-----------------------+            |          renderings<> o-----+                              |
|                                                                      +-------------------------+                                                                                  +-----------------------+                                    |
+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
"""

from flowpipe import Graph, Node


@Node(outputs=["camera_file"], metadata={"interpreter": "3dequalizer"})
def CreateCamera():
    """Creates a shot camera."""
    return {"camera_file": "/abs/camera.abc"}


@Node(outputs=["scene_file"], metadata={"interpreter": "maya"})
def MayaSceneGeneration(camera_file):
    """Creates a Maya scene file for rendering."""
    return {"scene_file": "/usd/scene.usd"}


@Node(outputs=["renderings"], metadata={"interpreter": "houdini"})
def HoudiniRender(frames, scene_file):
    """Creates a Houdini scene file for rendering."""
    return {"renderings": "/renderings/file.%04d.exr"}


@Node(outputs=["images"])
def CheckImages(images):
    """Check if the images are valid and return them."""
    return {"images": images}


@Node(outputs=["slapcomp"], metadata={"interpreter": "nuke"})
def CreateSlapComp(images, template):
    """Create a nuke slapcomp scene file from the given images and template."""
    return {"slapcomp": "slapcomp.nk"}


@Node(outputs=["renderings"], metadata={"interpreter": "nuke"})
def NukeRender(frames, scene_file):
    """Renders the slapcomp scene file using Nuke."""
    return {"renderings": "/renderings/file.%04d.exr"}


@Node(outputs=["quicktime"])
def Quicktime(images):
    """Create a quicktime movie from the rendered images."""
    return {"quicktime": "resulting.mov"}


@Node(outputs=["status"])
def UpdateDatabase(id_, images):
    """Update the database entries of the given asset with the given data."""
    return {"status": True}

def complex_cg_render(frames, batch_size):
    graph = Graph(name="Rendering")

    slapcomp = CreateSlapComp(graph=graph, template="nuke_template.nk")
    update_database = UpdateDatabase(graph=graph, id_=123456)
    
    camera_creation = CreateCamera(graph=graph)
    scene_creation = MayaSceneGeneration(graph=graph)

    camera_creation.outputs["camera_file"].connect(
        scene_creation.inputs["camera_file"]
    )

    for i in range(0, frames, batch_size):
        houdini_render = HoudiniRender(
            name="HoudiniRender{0}-{1}".format(i, i + batch_size),
            graph=graph,
            frames=range(i, i + batch_size),
            scene_file="/scene/for/rendering.ma",
        )
        scene_creation.outputs["scene_file"].connect(
            houdini_render.inputs["scene_file"]
        )
        check_images = CheckImages(
            name="CheckImages{0}-{1}".format(i, i + batch_size), graph=graph
        )
        houdini_render.outputs["renderings"].connect(
            check_images.inputs["images"]
        )
        check_images.outputs["images"].connect(
            slapcomp.inputs["images"][str(i)]
        )
        check_images.outputs["images"].connect(
            update_database.inputs["images"][str(i)]
        )

    quicktime = Quicktime()

    for i in range(0, frames, batch_size):
        nuke_render = NukeRender(
            name="NukeRender{0}-{1}".format(i, i + batch_size),
            graph=graph,
            frames=range(i, i + batch_size),
        )
        slapcomp.outputs["slapcomp"].connect(nuke_render.inputs["scene_file"])
        nuke_render.outputs["renderings"].connect(
            quicktime.inputs["images"][str(i)]
        )

    print(graph)


if __name__ == "__main__":
    complex_cg_render(30, 10)
