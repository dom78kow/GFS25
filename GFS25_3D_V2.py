from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, Spotlight, Vec4, Vec3, CardMaker, loadPrcFileData, TextNode
from panda3d.core import Texture, TextureStage, SamplerState, Material, Fog
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
import math
import sys
import os

# WINDOW & HIGH-END GRAPHICS SPECIFICATIONS
loadPrcFileData("", "window-title Farming Simulator 25 3D - Ultimate Edition")
loadPrcFileData("", "win-size 1200 750")
loadPrcFileData("", "fullscreen #f")
loadPrcFileData("", "sync-video #t")
loadPrcFileData("", "shadow-depth-bits 24")

# CRITICAL OBJ FORMAT CAPABILITY ENGINE ENABLER
loadPrcFileData("", "load-file-type p3assimp")


class FarmingSimulator3D(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.accept("escape", sys.exit)

        # =========================================================
        # REALISTIC EXPONENTIAL FOG ENGINE
        # =========================================================
        self.horizon_fog = Fog("AtmosphericFog")
        self.horizon_fog.set_color(0.53, 0.68, 0.88)  # Soft daylight blue gradient
        self.horizon_fog.set_mode(Fog.M_exponential)
        self.horizon_fog.set_exp_density(0.0075)  # Perfectly balances far field visibility ranges
        self.render.set_fog(self.horizon_fog)

        # 1. OPTIMIZED LEVEL-OF-DETAIL STREAMING MATRIX
        self.field_root = self.render.attach_new_node("FieldRoot")
        self.active_chunks = {}
        self.plowed_tiles = set()

        # Injects text layout parsing modules
        self.custom_map_data = {}
        self.load_layout_from_text_file()

        try:
            self.ground_tex = self.loader.load_texture("textures/cultivated.png")
            self.ground_tex.set_minfilter(SamplerState.FT_linear_mipmap_linear)
            self.ground_tex.set_magfilter(SamplerState.FT_linear)
            print("Successfully loaded cultivated.png with hardware texture streaming.")
        except Exception as e:
            print(f"Texture file fallback alert: {e}")
            self.ground_tex = None

        # Modulate mixing config: Merges material color layers dynamically onto textures
        self.crop_stage = TextureStage('crop_blender_layer')
        self.crop_stage.set_mode(TextureStage.M_modulate)

        # UPGRADED HIGH-REALISM GROUND FIELD MATERIALS
        self.terrain_material = Material()
        self.terrain_material.set_ambient(Vec4(0.75, 0.75, 0.75, 1.0))
        self.terrain_material.set_diffuse(Vec4(0.85, 0.85, 0.85, 1.0))
        self.terrain_material.set_specular(Vec4(0.12, 0.10, 0.08, 1.0))  # Gives dry soil a subtle crisp reflection
        self.terrain_material.set_shininess(4.0)
        self.field_root.set_material(self.terrain_material)
        # =========================================================
        # 2. LOAD TRACTOR MODEL MESH WITH GLOSS REFLECTION PIPELINE
        # =========================================================
        try:
            self.tractor = self.loader.load_model("models/tractor.obj")
            self.tractor.set_scale(0.33, 0.33, 0.33)
            self.tractor.set_h(-90)

            # Rich agricultural green base tone
            tractor_color = Vec4(0.08, 0.38, 0.12, 1.0)  # Deep John Deere Green
            self.tractor.set_color(tractor_color)
            self.tractor.set_two_sided(True)

            # This configures an explicit material mapping layer so the shader
            # generates realistic specular highlights across your vehicle panels.
            tractor_mat = Material()
            tractor_mat.set_ambient(Vec4(0.4, 0.4, 0.4, 1.0))
            tractor_mat.set_diffuse(Vec4(0.6, 0.6, 0.6, 1.0))
            tractor_mat.set_specular(Vec4(0.7, 0.7, 0.7, 1.0))  # Authentic semi-gloss metallic polish shine
            tractor_mat.set_shininess(32.0)  # Sharpens light beam highlights
            self.tractor.set_material(tractor_mat)
            print("Successfully initialized tractor geometries and gloss reflection layers.")
        except Exception as e:
            print(f"Could not load OBJ file ({e}), falling back to a placeholder block.")
            self.tractor = self.loader.load_model("models/box")
            self.tractor.set_scale(0.4, 0.66, 0.5)
            self.tractor.set_h(-90)

        self.tractor.reparent_to(self.render)
        self.tractor.set_pos(0, 0, 0)

        # =========================================================
        # CINEMATIC THREE-TIER LIGHTING STUDIO RIGS
        # =========================================================
        # Primary Cinematic Sunlight Direction Caster
        self.sun_light = DirectionalLight('cinematic_sun')
        self.sun_light.set_color(Vec4(1.2, 1.15, 1.02, 1.0))  # Golden noon sun intensity
        self.sun_light.set_shadow_caster(True, 2400, 2400)  # Precision shadow map canvas bounds
        lens = self.sun_light.get_lens()
        lens.set_film_size(24, 28)
        lens.set_near_far(5, 85)
        self.sun_np = self.render.attach_new_node(self.sun_light)
        self.sun_np.set_hpr(45, -48, 0)
        self.render.set_light(self.sun_np)

        # Ambient Sky Fill: Upgraded color parameters to blend realistically with background fog
        self.sky_light = AmbientLight('ambient_sky')
        self.sky_light.set_color(Vec4(0.48, 0.56, 0.68, 1.0))
        self.sky_np = self.render.attach_new_node(self.sky_light)
        self.render.set_light(self.sky_np)

        # Ground Soil Radiosity Bounce Light: Simulates light reflecting off dirt to illuminate the chassis underside
        self.bounce_light = DirectionalLight('ground_bounce')
        self.bounce_light.set_color(Vec4(0.25, 0.20, 0.15, 1.0))  # Warm dirt glow
        self.bounce_np = self.render.attach_new_node(self.bounce_light)
        self.bounce_np.set_hpr(45, 48, 0)
        self.render.set_light(self.bounce_np)

        # Re-balanced background clear palette to generate a smooth atmospheric morning look
        self.set_background_color(0.53, 0.68, 0.88)
        self.day_time = 12.0

        # VEHICLE HIGHLIGHT HEADLIGHT SPOTLIGHT CONSTRUCT
        self.headlight = Spotlight('tractor_headlight')
        self.headlight.set_color(Vec4(4.0, 4.0, 3.2, 1.0))  # Vivid Halogen Glow
        self.headlight.get_lens().set_fov(54)
        self.headlight.get_lens().set_near_far(1, 45)
        self.headlight_np = self.tractor.attach_new_node(self.headlight)
        self.headlight_np.set_pos(0, 1.4, 0.7)
        self.headlight_np.set_hpr(0, -12, 0)

        self.headlights_on = False
        self.accept("f", self.toggle_headlights)
        # =========================================================
        # MODERN SIMULATOR HUD CONFIGURATION (FS25 STYLE)
        # =========================================================
        # FIXED: Swapped out the broken borderColor attribute for native frameStyle and
        # flat relief behaviors to render crisp, high-definition panel frames.
        self.top_frame = DirectFrame(
            frameSize=(-0.52, 0.0, -0.18, 0.0),
            pos=(0, 0, 0),
            parent=self.a2dTopRight,
            frameColor=(0.05, 0.07, 0.09, 0.78),  # Clean dark-translucent slate backing
            relief=1  # Enforces standard flat geometric container shading
        )

        self.hud_day = OnscreenText(
            text="DAY 1", scale=0.032, fg=(0.6, 0.65, 0.7, 1),
            align=TextNode.ALeft, parent=self.top_frame, pos=(-0.48, -0.06),
            shadow=(0, 0, 0, 0.5)
        )
        self.hud_money = OnscreenText(
            text="$12,450", scale=0.058, fg=(0.22, 0.82, 0.40, 1),
            align=TextNode.ARight, parent=self.top_frame, pos=(-0.04, -0.07)
        )
        self.hud_clock = OnscreenText(
            text="12:00", scale=0.034, fg=(0.90, 0.92, 0.95, 1),
            align=TextNode.ARight, parent=self.top_frame, pos=(-0.04, -0.14)
        )

        self.left_frame = DirectFrame(
            frameSize=(0.0, 0.72, 0.0, 0.22),
            pos=(0, 0, 0),
            parent=self.a2dBottomLeft,
            frameColor=(0.05, 0.07, 0.09, 0.78),
            relief=1
        )

        self.hud_equip = OnscreenText(
            text="[ VEHICLE TELEMETRY LOGGER ]\nMODEL: DEUTZ AGROTRON D30\nTOOL: CR-30 HEAVY FIELD PLOW\nENGINE: ACTIVE\nPOSITION: X 0.0 / Y 0.0",
            scale=0.026, fg=(0.85, 0.9, 0.9, 1), align=TextNode.ALeft, parent=self.left_frame, pos=(0.04, 0.17))

        self.right_frame = DirectFrame(frameColor=(0.03, 0.04, 0.05, 0.75), frameSize=(-0.85, 0.0, 0.0, 0.46),
                                       pos=(0, 0, 0), parent=self.a2dBottomRight)

        self.dial_center = self.right_frame.attach_new_node("DialCenter")
        self.dial_center.set_pos(-0.52, 0, 0.24)
        self.dial_center.set_r(9.0)

        self.hud_speed = OnscreenText(text="0", scale=0.12, fg=(1, 1, 1, 1), align=TextNode.ACenter,
                                      parent=self.dial_center, pos=(0.0, -0.03))
        self.hud_unit = OnscreenText(text="KM/H", scale=0.026, fg=(0.4, 0.7, 0.1, 1), align=TextNode.ACenter,
                                     parent=self.dial_center, pos=(0.0, -0.09))
        self.hud_hours = OnscreenText(text="000.0h", scale=0.028, fg=(0.8, 0.82, 0.85, 1), align=TextNode.ACenter,
                                      parent=self.dial_center, pos=(0.0, -0.16))
        self.hud_speed.set_r(-9.0)
        self.hud_unit.set_r(-9.0)
        self.hud_hours.set_r(-9.0)

        self.rpm_segments = []
        self.total_ticks = 28
        segment_cm = CardMaker('rpm_block')
        segment_cm.set_frame(-0.012, 0.012, 0.14, 0.17)
        for i in range(self.total_ticks):
            angle = 220.0 + (i * (260.0 / (self.total_ticks - 1)))
            seg_np = self.dial_center.attach_new_node(segment_cm.generate())
            seg_np.set_r(angle)
            seg_np.set_color(0.12, 0.15, 0.15, 1.0)
            self.rpm_segments.append(seg_np)

        self.gear_nodes = {}
        gear_labels = [("D", 0.24), ("N", 0.17), ("R", 0.10)]
        for label, y_pos in gear_labels:
            bg_cm = CardMaker('gear_circle_fallback')
            bg_cm.set_frame(-0.035, 0.035, -0.035, 0.035)
            circle_np = self.right_frame.attach_new_node(bg_cm.generate())
            circle_np.set_pos(-0.16, 0, y_pos)
            circle_np.set_color(0.08, 0.10, 0.12, 1.0)
            text_np = OnscreenText(text=label, scale=0.035, fg=(0.4, 0.45, 0.5, 1), align=TextNode.ACenter,
                                   parent=circle_np, pos=(0.0, -0.012))
            self.gear_nodes[label] = {"bg": circle_np, "txt": text_np}

        bar_cm = CardMaker('vertical_monitor_fluid')
        bar_cm.set_frame(0.0, 0.02, 0.0, 0.20)
        self.fuel_bg = self.right_frame.attach_new_node(bar_cm.generate())
        self.fuel_bg.set_pos(-0.06, 0, 0.07)
        self.fuel_bg.set_color(0.1, 0.12, 0.14, 1)
        self.hud_fuel_bar = self.right_frame.attach_new_node(bar_cm.generate())
        self.hud_fuel_bar.set_pos(-0.06, 0, 0.07)
        self.hud_fuel_bar.set_color(0.95, 0.6, 0.02, 1)

        self.speed, self.heading = 0.0, 0.0
        self.max_transport_speed = 11.5
        self.max_reverse_speed = -4.0
        self.acceleration_rate = 6.0
        self.braking_decay = 12.0
        self.turn_speed, self.fuel = 55.0, 100.0
        self.current_rpm_pct = 0.08

        self.disable_mouse()
        self.cam_distance, self.cam_height_angle, self.cam_orbit_offset = 14.0, 22.0, -25.0
        self.is_mouse_dragging = False
        self.last_mouse_x, self.last_mouse_y = 0.0, 0.0

        self.accept("mouse3", self.start_drag)
        self.accept("mouse3-up", self.stop_drag)
        self.accept("wheel_up", self.zoom_camera, [-1.5])
        self.accept("wheel_down", self.zoom_camera, [1.5])
        self.accept("mouse2", self.reset_camera_view)

        self.taskMgr.add(self.update_simulation, "PhysicsAndCameraUpdateTask")

    def load_layout_from_text_file(self):
        maps_folder = "maps"
        file_name = "map1.txt"
        file_path = os.path.join(maps_folder, file_name)

        if not os.path.exists(maps_folder):
            os.makedirs(maps_folder)

        if not os.path.exists(file_path):
            print(f"Layout data file missing. Spawning standard default configurations at {file_path}...")
            fallback_layout = [
                "................................",
                ".....WWWWWWWW....CCCCCCCC.......",
                ".....WWWWWWWW....CCCCCCCC.......",
                ".....WWWWWWWW....CCCCCCCC.......",
                "................................",
                ".........#######................",
                ".........#######................",
                ".........#######................",
                "................................"
            ]
            with open(file_path, "w") as f:
                f.write("\n".join(fallback_layout))

        try:
            with open(file_path, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            height = len(lines)
            for r_idx, line in enumerate(lines):
                width = len(line)
                for c_idx, char in enumerate(line):
                    cx = c_idx - (width // 2)
                    cy = (height // 2) - r_idx
                    self.custom_map_data[(cx, cy)] = char.upper()
            print(f"Successfully configured file framework maps: Loaded {len(self.custom_map_data)} active sectors.")
        except Exception as e:
            print(f"Failed to process external layouts module structural map: {e}")

    def toggle_headlights(self):
        # STANDALONE METHOD LEVEL: Synchronized clean indents to fix initialization lookup errors
        self.headlights_on = not self.headlights_on
        if self.headlights_on:
            self.render.set_light(self.headlight_np)
        else:
            self.render.clear_light(self.headlight_np)

    def generate_procedural_rounded_texture(self):
        # Kept signature format alive to satisfy internal layout fallbacks safely
        tex = Texture("hud_round_mask")
        tex.setup_2d_texture(4, 4, Texture.T_unsigned_byte, Texture.F_rgba)
        tex.set_ram_image(bytes([255, 255, 255, 255] * 16))
        return tex

    def start_drag(self):
        if self.mouseWatcherNode.has_mouse():
            self.last_mouse_x = self.mouseWatcherNode.get_mouse_x()
            self.last_mouse_y = self.mouseWatcherNode.get_mouse_y()
            self.is_mouse_dragging = True

    def stop_drag(self):
        self.is_mouse_dragging = False

    def zoom_camera(self, amount):
        self.cam_distance = max(6.0, min(45.0, self.cam_distance + amount))

    def reset_camera_view(self):
        self.cam_orbit_offset, self.cam_height_angle, self.cam_distance = -25.0, 22.0, 14.0

    def update_simulation(self, task):
        key_map = {"forward": self.mouseWatcherNode.is_button_down("w"),
                   "reverse": self.mouseWatcherNode.is_button_down("s"),
                   "left": self.mouseWatcherNode.is_button_down("a"),
                   "right": self.mouseWatcherNode.is_button_down("d")}

        dt = globalClock.get_dt()
        if dt > 0.15: return Task.cont

        self.day_time = 10.0 if self.day_time >= 17.0 else self.day_time + dt * 0.05
        self.hud_clock.setText(f"{int(self.day_time):02d}:{int((self.day_time - int(self.day_time)) * 60):02d}")

        pos_x, pos_y = self.tractor.get_x(), self.tractor.get_y()
        center_x, center_y = int(round(pos_x / 5.0)), int(round(pos_y / 5.0))

        # High-Performance GPU Field Tiling Loop Matrix
        view_radius = 16
        needed_chunks = set()
        cm = CardMaker('ground_tile')
        cm.set_frame(-2.5, 2.5, -2.5, 2.5)

        for cx in range(center_x - view_radius, center_x + view_radius + 1):
            for cy in range(center_y - view_radius, center_y + view_radius + 1):
                needed_chunks.add((cx, cy))
                if (cx, cy) not in self.active_chunks:
                    chunk_np = self.field_root.attach_new_node(cm.generate())
                    chunk_np.set_pos(cx * 5.0, cy * 5.0, -0.1)
                    chunk_np.set_p(-90)

                    if self.ground_tex:
                        chunk_np.set_texture(self.crop_stage, self.ground_tex)

                    # Extract attributes matching map1.txt configurations
                    cell_type = self.custom_map_data.get((cx, cy), '.')

                    if (cx, cy) in self.plowed_tiles:
                        state = "plowed"
                        chunk_np.set_color(0.22, 0.14, 0.07, 1.0)
                    elif cell_type == '#':
                        state = "plowed"
                        chunk_np.set_color(0.50, 0.38, 0.28, 1.0)  # Organic topsoil brown
                    elif cell_type == 'W':
                        state = "wheat"
                        chunk_np.set_color(0.92, 0.76, 0.32, 1.0)  # Deep agricultural amber wheat
                    elif cell_type == 'C':
                        state = "canola"
                        chunk_np.set_color(0.92, 0.85, 0.12, 1.0)  # Radiant canola yellow
                    else:
                        state = "grass"
                        chunk_np.set_color(0.26, 0.58, 0.26, 1.0)  # Countryside green field meadow

                    self.active_chunks[(cx, cy)] = {"node": chunk_np, "state": state}

        for dead_chunk in list(self.active_chunks.keys()):
            if dead_chunk not in needed_chunks:
                self.active_chunks[dead_chunk]["node"].remove_node()
                del self.active_chunks[dead_chunk]

        current_chunk = self.active_chunks.get((center_x, center_y))
        footing_state = current_chunk["state"] if current_chunk else "grass"
        is_plowing = (footing_state == "plowed" and self.speed > 0.05)

        current_max_speed = 2.8 if is_plowing else self.max_transport_speed
        self.hud_equip.setText(
            f"[ VEHICLE TELEMETRY LOGGER ]\nMODEL: DEUTZ AGROTRON D30\nTOOL: CR-30 HEAVY FIELD PLOW\nENGINE: ACTIVE\nPOSITION: X {pos_x:.1f} / Y {pos_y:.1f}")

        if abs(self.speed) > 0.1:
            dir_mod = 1.0 if self.speed > 0 else -1.0
            if key_map["left"]:  self.heading += self.turn_speed * dt * dir_mod
            if key_map["right"]: self.heading -= self.turn_speed * dt * dir_mod

        self.tractor.set_h(self.heading - 90)

        if key_map["forward"] and self.fuel > 0:
            self.speed = min(current_max_speed, self.speed + self.acceleration_rate * dt)
            self.fuel = max(0.0, self.fuel - (0.24 * dt if is_plowing else 0.12 * dt))
        elif key_map["reverse"] and self.fuel > 0:
            self.speed = max(self.max_reverse_speed, self.speed - self.acceleration_rate * dt)
            self.fuel = max(0.0, self.fuel - 0.09 * dt)
        else:
            if self.speed > 0:
                self.speed = max(0.0, self.speed - self.braking_decay * dt)
            else:
                self.speed = min(0.0, self.speed + self.braking_decay * dt)

        if self.speed > current_max_speed: self.speed = max(current_max_speed, self.speed - 8.0 * dt)

        rad = math.radians(self.heading)
        self.tractor.set_pos(pos_x - self.speed * dt * math.sin(rad), pos_y + self.speed * dt * math.cos(rad), 0)

        self.sun_np.set_pos(self.tractor.get_x() - 10.0, self.tractor.get_y() - 10.0, 16.0)

        if self.is_mouse_dragging and self.mouseWatcherNode.has_mouse():
            mx, my = self.mouseWatcherNode.get_mouse_x(), self.mouseWatcherNode.get_mouse_y()
            self.cam_orbit_offset -= (mx - self.last_mouse_x) * 160.0
            self.cam_height_angle = max(5.0, min(80.0, self.cam_height_angle - (my - self.last_mouse_y) * 90.0))
            self.last_mouse_x, self.last_mouse_y = mx, my

        v_rad, p_rad = math.radians(self.heading + self.cam_orbit_offset), math.radians(self.cam_height_angle)
        target_cam_pos = Vec3(
            self.tractor.get_x() + self.cam_distance * math.cos(p_rad) * math.sin(v_rad),
            self.tractor.get_y() - self.cam_distance * math.cos(p_rad) * math.cos(v_rad),
            self.tractor.get_z() + self.cam_distance * math.sin(p_rad)
        )

        self.camera.set_pos(self.camera.get_pos() + (target_cam_pos - self.camera.get_pos()) * 8.0 * dt)
        self.camera.look_at(self.tractor.get_pos() + (0, 0, 1.0))

        display_speed = int(abs(self.speed) * 3.6)
        self.hud_speed.setText(f"{display_speed}")

        if key_map["forward"] or key_map["reverse"]:
            target_rpm = 0.82 if is_plowing else 0.35 + (abs(self.speed) / self.max_transport_speed) * 0.45
        else:
            target_rpm = 0.24 if self.speed > 0.1 else 0.08

        self.current_rpm_pct += (target_rpm - self.current_rpm_pct) * 3.0 * dt
        lit_count = int(min(1.0, max(0.0, self.current_rpm_pct)) * self.total_ticks)

        for idx, seg_node in enumerate(self.rpm_segments):
            if idx <= lit_count:
                seg_node.set_color(0.55, 0.78, 0.05, 1.0)
            else:
                seg_node.set_color(0.18, 0.22, 0.22, 1.0)

        current_gear = "D" if self.speed > 0.05 else ("R" if self.speed < -0.05 else "N")
        for gear_id, assets in self.gear_nodes.items():
            if gear_id == current_gear:
                assets["bg"].set_color(0.55, 0.78, 0.05, 1.0)
                assets["txt"].setColor(Vec4(1, 1, 1, 1))
            else:
                assets["bg"].set_color(0.08, 0.10, 0.12, 1.0)
                assets["txt"].setColor(Vec4(0.4, 0.45, 0.5, 1))

        fuel_ratio = self.fuel / 100.0
        self.hud_fuel_bar.set_scale(1, 1, fuel_ratio)
        if self.fuel < 20:
            self.hud_fuel_bar.set_color(0.85, 0.25, 0.23, 1)
        else:
            self.hud_fuel_bar.set_color(0.95, 0.6, 0.02, 1)

        # Real-Time Dynamic Plowing Modification Matrix
        if is_plowing and (center_x, center_y) not in self.plowed_tiles:
            self.plowed_tiles.add((center_x, center_y))
            if (center_x, center_y) in self.active_chunks:
                self.active_chunks[(center_x, center_y)]["node"].set_color(0.22, 0.14, 0.07, 1.0)
                self.active_chunks[(center_x, center_y)]["state"] = "plowed"

        return Task.cont


# CORE INITIALIZATION ENTRY SYSTEM MAIN THREAD LAUNCHER
if __name__ == "__main__":
    app = FarmingSimulator3D()
    app.run()
