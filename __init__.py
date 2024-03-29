import bpy
from pathlib import Path
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
import os
import bpy
import sys
import importlib.util
import re
from bpy.types import Panel, Operator
from bpy.props import IntProperty

# Attempt to import Pillow at the start of your script
try:
    from PIL import Image, __version__ as PIL_VERSION
    print("Pillow is already installed.")
except ImportError:
    def install_pillow():
        try:
            print("Pillow is not installed. Attempting to install...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Pillow successfully installed. Please restart Blender.")
        except subprocess.CalledProcessError as e:
            print("Failed to install Pillow. Please install it manually. Error:", e)
        except Exception as e:
            print(f"An unexpected error occurred while trying to install Pillow: {e}")
    install_pillow()
    # After attempting installation, try importing again
    try:
        from PIL import Image, __version__ as PIL_VERSION
    except ImportError:
        print("Failed to import Pillow after installation attempt. Please restart Blender and try again.")

bl_info = {
    "name": "NJ Image Tools",
    "author": "Nomadic Jester",
    "version": (1, 0),
    "blender": (4, 1, 0),
    "location": "Properties > Material > TexConv",
    "description": "Convert images to DDS format using TexConv",
    "category": "Material"
}

addon_dir = Path(__file__).parent
texconv_exe = addon_dir / "texconv.exe"

# Generalized function to convert image files
def convert_file(input_file, output_file, file_type, compression_format=None):
    command = [str(texconv_exe), "-nologo", "-pow2", "-y", "-ft", file_type, str(input_file), "-o", str(output_file.parent)]
    if compression_format:
        command.extend(["-f", compression_format])
    if file_type.upper() == "PNG":
        command.append("-srgb")
        command.append("on")
    else:
        command.append("-srgb")
        command.append("off")
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        print(f"Error converting file: {result.stderr.decode()}")

# Function to fix mip maps for a single image
def fix_mip_maps_for_image(image_path, output_folder):
    image_path = Path(image_path)
    output_folder = Path(output_folder)
    fixed_dds_path = output_folder / image_path.name
    temp_png_path = fixed_dds_path.with_suffix(".png")
    convert_file(image_path, temp_png_path, "PNG")
    material_compression_format = get_compression_format_from_name(image_path.name)
    convert_file(temp_png_path, fixed_dds_path, "DDS", material_compression_format or "BC3_UNORM")
    temp_png_path.unlink()  # Delete the temporary PNG file

# Function to fix mip maps for textures in a folder
def fix_folder_mip_maps(folder_path, output_folder):
    folder_path = Path(folder_path)
    output_folder = Path(output_folder)
    with ThreadPoolExecutor(max_workers=4) as executor:  # Limiting to 4 workers
        for file_path in folder_path.glob('*.dds'):
            material_compression_format = get_compression_format_from_name(file_path.name)
            executor.submit(convert_file, file_path, output_folder / file_path.name, "DDS", material_compression_format or "BC3_UNORM")

# Function to get the compression format from the material name
def get_compression_format_from_name(material_name):
    compression_formats = {
        "dxt1": "BC1_UNORM",
        "dxt3": "BC2_UNORM",
        "dxt5": "BC3_UNORM"
    }
    for key, value in compression_formats.items():
        if key in material_name.lower():
            return value
    return None

# GUI Panel
class ConvertToDDSPanel(bpy.types.Panel):
    bl_label = "NJ-TexConv"
    bl_idname = "OBJECT_PT_convert_to_dds"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row(align=True)
        row.prop(scene, "compression_format", text="Compression Format")

        row = layout.row(align=True)
        row.operator("object.convert_to_dds", text="Convert")
        row.operator("object.fix_mip_maps", text="Fix Mip Maps")

        layout.separator()

        layout.label(text="Folder Operations:")

        row = layout.row(align=True)
        if scene.selected_folder:
            absolute_folder_path = Path(bpy.path.abspath(scene.selected_folder)).resolve()
            display_path = str(absolute_folder_path)
        else:
            display_path = "No folder selected."
        row.prop(scene, "selected_folder", text="Folder")
        row.operator("object.fix_folder_mip_maps", text="Fix Mip Maps")

        layout.label(text=f"Selected Folder: {display_path}")

# Operator to execute DDS conversion
class OBJECT_OT_ConvertToDDS(bpy.types.Operator):
    bl_idname = "object.convert_to_dds"
    bl_label = "Convert to DDS"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_object = context.active_object
        blend_file_dir = bpy.path.abspath("//")
        dds_dir = Path(blend_file_dir) / "dds-textures"
        dds_dir.mkdir(parents=True, exist_ok=True)

        for material_slot in selected_object.material_slots:
            material = material_slot.material
            if material and material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        image_path = bpy.path.abspath(node.image.filepath)
                        if Path(image_path).exists():
                            if image_path.lower().endswith('.dds'):
                                shutil.move(image_path, dds_dir / Path(image_path).name)
                            else:
                                dds_filename = Path(image_path).stem + ".dds"
                                dds_path = dds_dir / dds_filename
                                material_compression_format = get_compression_format_from_name(material.name)
                                if material_compression_format:
                                    convert_file(Path(image_path), dds_path, "DDS", material_compression_format)
                                else:
                                    original_compression_format = get_compression_format_from_name(Path(image_path).name)
                                    if original_compression_format:
                                        convert_file(Path(image_path), dds_path, "DDS", original_compression_format)
                                    else:
                                        convert_file(Path(image_path), dds_path, "DDS", context.scene.compression_format)
                                node.image.filepath = bpy.path.relpath(str(dds_path))
                                bpy.data.images[node.image.name].name = dds_filename

        self.report({'INFO'}, "DDS conversion complete.")
        return {'FINISHED'}

# Operator to fix mip maps
class OBJECT_OT_FixMipMaps(bpy.types.Operator):
    bl_idname = "object.fix_mip_maps"
    bl_label = "Fix Mip Maps"

    def execute(self, context):
        selected_object = context.active_object
        blend_file_dir = bpy.path.abspath("//")
        fixed_dds_dir = Path(blend_file_dir) / "fixed-dds-textures"
        fixed_dds_dir.mkdir(parents=True, exist_ok=True)

        for material_slot in selected_object.material_slots:
            material = material_slot.material
            if material and material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        image_path = bpy.path.abspath(node.image.filepath)
                        if Path(image_path).exists() and image_path.lower().endswith('.dds'):
                            fix_mip_maps_for_image(image_path, fixed_dds_dir)
                            node.image.filepath = bpy.path.relpath(str(fixed_dds_dir / Path(image_path).name))

        self.report({'INFO'}, "Mip Maps fixed.")
        return {'FINISHED'}

# Operator to fix mip maps for textures in a folder
class OBJECT_OT_FixFolderMipMaps(bpy.types.Operator):
    bl_idname = "object.fix_folder_mip_maps"
    bl_label = "Fix Folder Mip Maps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_folder = context.scene.selected_folder

        if selected_folder:
            # Convert the selected folder path to an absolute path
            absolute_folder_path = Path(bpy.path.abspath(selected_folder)).resolve()

            fixed_dds_folder = absolute_folder_path / "Fixed_DDS"
            fixed_dds_folder.mkdir(parents=True, exist_ok=True)

            fix_folder_mip_maps(absolute_folder_path, fixed_dds_folder)

            self.report({'INFO'}, "Folder mip maps fixed.")
        else:
            self.report({'ERROR'}, "No folder selected.")

        return {'FINISHED'}
    
class ResizeImagesPanel(Panel):
    bl_label = "NJ-Resize Images"
    bl_idname = "MATERIAL_PT_resize_images"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Preset Image Sizes:")
        layout.operator("image.set_preset_size", text="256x256").width = 256
        layout.operator("image.set_preset_size", text="512x512").width = 512
        layout.operator("image.set_preset_size", text="1024x1024").width = 1024

        layout.label(text="Custom Size:")
        row = layout.row()
        row.prop(scene, "custom_width")
        row.prop(scene, "custom_height")

        layout.operator("image.resize_images", text="Resize Images")

class SetPresetSizeOperator(Operator):
    bl_idname = "image.set_preset_size"
    bl_label = "Set Preset Size"
    bl_options = {'REGISTER', 'UNDO'}

    width: IntProperty(default=256)

    def execute(self, context):
        context.scene.custom_width = self.width
        context.scene.custom_height = self.width
        return {'FINISHED'}

class ResizeImagesOperator(Operator):
    bl_idname = "image.resize_images"
    bl_label = "Resize Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_object = context.active_object
        if selected_object:
            image_size = (context.scene.custom_width, context.scene.custom_height)
            self.resize_all_images(selected_object, image_size)
        return {'FINISHED'}

    def resize_all_images(self, obj, image_size):
        base_output_folder = bpy.path.abspath("//resized-images")
        os.makedirs(base_output_folder, exist_ok=True)

        for slot in obj.material_slots:
            material = slot.material
            if material and material.use_nodes:
                material_folder_name = f"{material.name}_{image_size[0]}x{image_size[1]}"
                material_output_folder = os.path.join(base_output_folder, material_folder_name)
                os.makedirs(material_output_folder, exist_ok=True)

                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        image = node.image
                        original_filepath = bpy.path.abspath(image.filepath)
                        file_extension = os.path.splitext(original_filepath)[1].lower()

                        if file_extension == '.dds':
                            # Raise an error if the file is a .dds file
                            self.report({'ERROR'}, "Resizing .dds files is not supported.")
                            return {'CANCELLED'}
                        else:
                            # Resize using Pillow for other formats
                            self.resize_image_with_pillow(original_filepath, material_output_folder, image_size, node)

        self.report({'INFO'}, "Image resizing complete.")
        return {'FINISHED'}

    def resize_image_with_pillow(self, input_path, output_folder, size, node):
        try:
            img = Image.open(input_path)
            img = img.resize(size, Image.LANCZOS)
            output_path = os.path.join(output_folder, os.path.basename(input_path))
            img.save(output_path)
            print(f"Resized image saved to: {output_path}")
            # Update the image node's file path
            node.image.filepath = bpy.path.relpath(output_path)
        except Exception as e:
            print(f"Failed to resize image {input_path}: {e}")

# Register classes
def register():
    bpy.utils.register_class(ResizeImagesPanel)
    bpy.utils.register_class(SetPresetSizeOperator)
    bpy.utils.register_class(ResizeImagesOperator)
    bpy.types.Scene.custom_width = IntProperty(name="Width", default=256)
    bpy.types.Scene.custom_height = IntProperty(name="Height", default=256)
    bpy.utils.register_class(ConvertToDDSPanel)
    bpy.utils.register_class(OBJECT_OT_ConvertToDDS)
    bpy.utils.register_class(OBJECT_OT_FixMipMaps)
    bpy.utils.register_class(OBJECT_OT_FixFolderMipMaps)
    bpy.types.Scene.compression_format = bpy.props.EnumProperty(
        items=[
            ("BC1_UNORM", "BC1_UNORM (DXT1)", ""),
            ("BC2_UNORM", "BC2_UNORM (DXT3)", ""),
            ("BC3_UNORM", "BC3_UNORM (DXT5)", ""),
            ("BC4_UNORM", "BC4_UNORM (ATI1)", ""),
            ("BC5_UNORM", "BC5_UNORM (3Dc)", ""),
            ("BC6H_UF16", "BC6H_UF16", ""),
            ("BC7_UNORM", "BC7_UNORM", "")
        ],
        name="Compression Format",
        description="Compression format for DDS conversion"
    )
    bpy.types.Scene.selected_folder = bpy.props.StringProperty(name="Selected Folder", description="Selected folder for texture operations", subtype='DIR_PATH')

def unregister():
    bpy.utils.unregister_class(ConvertToDDSPanel)
    bpy.utils.unregister_class(OBJECT_OT_ConvertToDDS)
    bpy.utils.unregister_class(OBJECT_OT_FixMipMaps)
    bpy.utils.unregister_class(OBJECT_OT_FixFolderMipMaps)
    del bpy.types.Scene.compression_format
    del bpy.types.Scene.selected_folder
    bpy.utils.unregister_class(ResizeImagesPanel)
    bpy.utils.unregister_class(SetPresetSizeOperator)
    bpy.utils.unregister_class(ResizeImagesOperator)
    del bpy.types.Scene.custom_width
    del bpy.types.Scene.custom_height

if __name__ == "__main__":
    register
