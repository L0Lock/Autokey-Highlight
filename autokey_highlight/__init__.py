import bpy
import gpu
from gpu_extras.batch import batch_for_shader

bl_info = {
    'name': 'Autokey Highlight',
    'author': 'Loïc \"Lauloque\" Dautry',
    'description': "Toggles a border in the viewport based on autokey state, with customizable color and width",
    'version': (1, 0, 1),
    'blender': (4, 3, 0),
    'category': 'System',
    'doc_url': "https://github.com/L0Lock/Autokey-Highlight",
    'support': 'COMMUNITY',
    'tracker_url': "https://github.com/L0Lock/Autokey-Highlight/issues",
}

draw_handle = None


def draw_callback_px():
    """Draws a border around the 3D viewport based on user preferences."""
    preferences = bpy.context.preferences.addons[__name__].preferences
    border_color = preferences.border_color
    border_width = preferences.border_width

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.line_width_set(border_width)
    gpu.state.blend_set('ALPHA')

    # Get viewport dimensions
    width, height = bpy.context.region.width, bpy.context.region.height

    # Define border positions
    positions = [
        (0, 0),
        (width, 0),
        (width, height),
        (0, height),
        (0, 0),
    ]

    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": positions})
    shader.uniform_float("color", border_color)
    batch.draw(shader)

    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def toggle_border():
    """Toggle the border based on the autokey state."""
    global draw_handle

    autokey_enabled = bpy.context.scene.tool_settings.use_keyframe_insert_auto

    if autokey_enabled and draw_handle is None:
        draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (), 'WINDOW', 'POST_PIXEL')
    elif not autokey_enabled and draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')
        draw_handle = None


@bpy.app.handlers.persistent
def monitor_autokey(dummy):
    """Monitor changes to the autokey state and update the border."""
    toggle_border()


class AutokeyBorderPreferences(bpy.types.AddonPreferences):
    """Preferences for the Autokey Border Highlight addon."""
    bl_idname = __name__

    border_color: bpy.props.FloatVectorProperty(
        name="Border Color",
        description="Color of the border",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.1, 0.1, 1.0),  # Default red color
        min=0.0, max=1.0,
    )
    border_width: bpy.props.IntProperty(
        name="Border Width",
        description="Width of the border",
        default=4,
        subtype='PIXEL',
        min=1,
        max=10,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Customize Border Appearance")
        layout.prop(self, "border_color")
        layout.prop(self, "border_width")


def init_toggle_border():
    """Initialize the toggle_border logic safely."""
    if bpy.context.scene:  # Ensure the scene is available
        toggle_border()
    return None  # Stop the timer after execution


def register():
    bpy.utils.register_class(AutokeyBorderPreferences)
    bpy.app.handlers.depsgraph_update_post.append(monitor_autokey)

    # Use a timer to safely defer the initialization
    bpy.app.timers.register(init_toggle_border)


def unregister():
    global draw_handle

    bpy.utils.unregister_class(AutokeyBorderPreferences)
    bpy.app.handlers.depsgraph_update_post.remove(monitor_autokey)

    if draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')
        draw_handle = None

if __name__ == "__main__":
    register()