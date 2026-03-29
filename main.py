import tkinter as tk
import math
import random

# =========================================================
# WINDOW SETUP
# =========================================================
root = tk.Tk()
root.title("Robot Arm Simulator")

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill="both", expand=True)

# =========================================================
# GLOBAL STATE (initialized later)
# =========================================================
desk_x1 = desk_y1 = desk_x2 = desk_y2 = 0
drop_x1 = drop_y1 = drop_x2 = drop_y2 = 0

# =========================================================
# OBJECTS
# =========================================================
objects = []
for i in range(10):
    objects.append({
        "name": f"ball_{i}",
        "x": random.randint(200, 800),
        "y": random.randint(200, 500)
    })

target = {"x": 400, "y": 300}
held_object = None

# =========================================================
# ARM BASE (EDGE TRACK)
# =========================================================
base_x = 0
base_y = 0
edge_pos = 0
perimeter = 1  # avoid division by zero initially

# =========================================================
# ARM CONFIG
# =========================================================
lengths = [100, 100, 80, 60]
angles = [0.0, 0.0, 0.0, 0.0]

# =========================================================
# UTILITY
# =========================================================
def distance(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

# =========================================================
# DESK RESIZING (RESPONSIVE)
# =========================================================
def update_desk_size(event=None):
    global desk_x1, desk_y1, desk_x2, desk_y2
    global drop_x1, drop_y1, drop_x2, drop_y2
    global perimeter

    width = canvas.winfo_width()
    height = canvas.winfo_height()

    margin = 50

    desk_x1 = margin
    desk_y1 = margin
    desk_x2 = width - margin
    desk_y2 = height - margin

    # Drop zone (top-left of desk)
    drop_x1 = desk_x1 + 20
    drop_y1 = desk_y1 + 20
    drop_x2 = desk_x1 + 120
    drop_y2 = desk_y1 + 120

    # Update perimeter
    perimeter = 2 * ((desk_x2 - desk_x1) + (desk_y2 - desk_y1))

canvas.bind("<Configure>", update_desk_size)

# =========================================================
# INPUT: TARGET
# =========================================================
def set_target(event):
    x = max(desk_x1, min(event.x, desk_x2))
    y = max(desk_y1, min(event.y, desk_y2))
    target["x"] = x
    target["y"] = y

canvas.bind("<Button-1>", set_target)
canvas.bind("<B1-Motion>", set_target)

# =========================================================
# INPUT: BASE MOVEMENT (EDGE LOOP)
# =========================================================
def move_base(event):
    global edge_pos

    step = 40

    if event.keysym == "a":
        edge_pos -= step
    elif event.keysym == "d":
        edge_pos += step

    if perimeter > 0:
        edge_pos %= perimeter

root.bind("<Key>", move_base)

# =========================================================
# EDGE → BASE POSITION
# =========================================================
def update_base_position():
    global base_x, base_y

    p = edge_pos
    width = desk_x2 - desk_x1
    height = desk_y2 - desk_y1

    if p < width:
        base_x = desk_x1 + p
        base_y = desk_y2

    elif p < width + height:
        base_x = desk_x2
        base_y = desk_y2 - (p - width)

    elif p < 2 * width + height:
        base_x = desk_x2 - (p - (width + height))
        base_y = desk_y1

    else:
        base_x = desk_x1
        base_y = desk_y1 + (p - (2 * width + height))

# =========================================================
# GRAB / DROP
# =========================================================
def grab(event):
    global held_object
    ex, ey = get_end_effector()

    for obj in objects:
        if distance(ex, ey, obj["x"], obj["y"]) < 25:
            held_object = obj
            print("Grabbed:", obj["name"])

def drop(event):
    global held_object

    if held_object:
        x, y = held_object["x"], held_object["y"]

        if drop_x1 <= x <= drop_x2 and drop_y1 <= y <= drop_y2:
            print("Delivered:", held_object["name"])

    held_object = None
    print("Dropped")

root.bind("g", grab)
root.bind("f", drop)

# =========================================================
# FORWARD KINEMATICS
# =========================================================
def get_joint_positions():
    x, y = base_x, base_y
    total_angle = 0
    points = [(x, y)]

    for i in range(len(lengths)):
        total_angle += angles[i]
        x += lengths[i] * math.cos(total_angle)
        y += lengths[i] * math.sin(total_angle)
        points.append((x, y))

    return points

def get_end_effector():
    return get_joint_positions()[-1]

# =========================================================
# CCD INVERSE KINEMATICS
# =========================================================
def update_angles():
    tx, ty = target["x"], target["y"]

    for i in reversed(range(len(angles))):
        points = get_joint_positions()

        joint_x, joint_y = points[i]
        end_x, end_y = points[-1]

        v1x = end_x - joint_x
        v1y = end_y - joint_y

        v2x = tx - joint_x
        v2y = ty - joint_y

        angle1 = math.atan2(v1y, v1x)
        angle2 = math.atan2(v2y, v2x)

        delta = angle2 - angle1

        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi

        angles[i] += delta * 0.4

# =========================================================
# DRAW
# =========================================================
def draw():
    canvas.delete("all")

    # Desk
    canvas.create_rectangle(desk_x1, desk_y1, desk_x2, desk_y2,
                            fill="#dddddd", outline="black")

    # Drop zone
    canvas.create_rectangle(drop_x1, drop_y1, drop_x2, drop_y2,
                            fill="#aaffaa", outline="green", width=2)

    canvas.create_text((drop_x1 + drop_x2)//2, drop_y1 - 10,
                       text="DROP ZONE")

    # Objects
    for obj in objects:
        color = "green" if obj == held_object else "blue"
        canvas.create_oval(obj["x"]-10, obj["y"]-10,
                           obj["x"]+10, obj["y"]+10,
                           fill=color)

    # Target
    canvas.create_oval(target["x"]-5, target["y"]-5,
                       target["x"]+5, target["y"]+5,
                       fill="red")

    # Arm
    points = get_joint_positions()

    for i in range(len(points)-1):
        canvas.create_line(points[i][0], points[i][1],
                           points[i+1][0], points[i+1][1],
                           width=4)

    # End effector
    ex, ey = points[-1]
    canvas.create_oval(ex-6, ey-6, ex+6, ey+6, fill="green")

# =========================================================
# MAIN LOOP
# =========================================================
def update():
    update_base_position()
    update_angles()

    ex, ey = get_end_effector()

    if held_object:
        held_object["x"] = ex
        held_object["y"] = ey

        # Clamp to desk
        held_object["x"] = max(desk_x1, min(held_object["x"], desk_x2))
        held_object["y"] = max(desk_y1, min(held_object["y"], desk_y2))

    draw()
    root.after(30, update)

# =========================================================
# START
# =========================================================
update_desk_size()
update()
root.mainloop()
