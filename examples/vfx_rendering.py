"""Demo a complex workflow of a rendering with a series of subsequent actions:

- Render a CG render out of Maya
- Check the resulting images for potential defects caused by potential server glitches
- Register the CG render in the database
- Create and render a slap comp
- Convert the rendered slapcomp to a quicktime

+---------------------------+          +----------------------+           +-------------------------+          +-----------------------+          +-----------------------+
|      MayaRender0-10       |          |   CheckImages0-10    |           |     CreateSlapComp      |          |    NukeRender0-10     |          |       Quicktime       |
|---------------------------|          |----------------------|           |-------------------------|          |-----------------------|          |-----------------------|
o frames<[0, 1, 2, >        |     +--->o images<>             |           % images                  |          o frames<[0, 1, 2, >    |          % images                |
o scene_file<"/scene/fo>    |     |    |               images o---------->o  images.0<>             |     +--->o scene_file<>          |     +--->o  images.0<>           |
|                renderings o-----+    +----------------------+      |--->o  images.10<>            |   --+    |            renderings o-----+--->o  images.10<>          |
+---------------------------+          +-----------------------+     |--->o  images.20<>            |     |    +-----------------------+     |--->o  images.20<>          |
+---------------------------+          |   CheckImages10-20    |     |    o template<"nuke_temp>    |     |    +-----------------------+     |    |             quicktime o
|      MayaRender10-20      |          |-----------------------|     |    |                slapcomp o---  |    |    NukeRender10-20    |     |    +-----------------------+
|---------------------------|     +--->o images<>              |     |    +-------------------------+     |    |-----------------------|     |
o frames<[10, 11, 1>        |     |    |                images o-----|    +-----------------------+       |    o frames<[10, 11, 1>    |     |
o scene_file<"/scene/fo>    |     |    +-----------------------+     |    |    UpdateDatabase     |       +--->o scene_file<>          |     |
|                renderings o-----+    +-----------------------+     |    |-----------------------|       |    |            renderings o-----+
+---------------------------+          |   CheckImages20-30    |     |    o id_<123456>           |       |    +-----------------------+     |
+---------------------------+          |-----------------------|     |    % images                |       |    +-----------------------+     |
|      MayaRender20-30      |     +--->o images<>              |     +--->o  images.0<>           |       |    |    NukeRender20-30    |     |
|---------------------------|     |    |                images o-----+--->o  images.10<>          |       |    |-----------------------|     |
o frames<[20, 21, 2>        |     |    +-----------------------+     +--->o  images.20<>          |       |    o frames<[20, 21, 2>    |     |
o scene_file<"/scene/fo>    |     |                                       |                status o       +--->o scene_file<>          |     |
|                renderings o-----+                                       +-----------------------+            |            renderings o-----+
+---------------------------+                                                                                  +-----------------------+
"""

from flowpipe import Graph, Node


@Node(outputs=["renderings"], metadata={"interpreter": "maya"})
def MayaRender(frames, scene_file):
    return {"renderings": "/renderings/file.%04d.exr"}


@Node(outputs=["images"])
def CheckImages(images):
    return {"images": images}


@Node(outputs=["slapcomp"])
def CreateSlapComp(images, template):
    return {"slapcomp": "slapcomp.nk"}


@Node(outputs=["renderings"], metadata={"interpreter": "nuke"})
def NukeRender(frames, scene_file):
    return {"renderings": "/renderings/file.%04d.exr"}


@Node(outputs=["quicktime"])
def Quicktime(images):
    return {"quicktime": "resulting.mov"}


@Node(outputs=["status"])
def UpdateDatabase(id_, images):
    """Update the database entries of the given asset with the given data."""
    return {"status": True}


def complex_cg_render(frames, batch_size):
    graph = Graph(name="Rendering")

    slapcomp = CreateSlapComp(graph=graph, template="nuke_template.nk")
    update_database = UpdateDatabase(graph=graph, id_=123456)

    for i in range(0, frames, batch_size):
        maya_render = MayaRender(
            name="MayaRender{0}-{1}".format(i, i + batch_size),
            graph=graph,
            frames=range(i, i + batch_size),
            scene_file="/scene/for/rendering.ma",
        )
        check_images = CheckImages(
            name="CheckImages{0}-{1}".format(i, i + batch_size), graph=graph
        )
        maya_render.outputs["renderings"].connect(
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
