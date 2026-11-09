"""A villager body shared by NPC batch 2 (woman, cook, child, smith): the same drawing as batch 1
(npc_common), with the layer order and the motion in one place, the look in each character's maps.

Order of drawing (back to front):
  front / back view   legs -> props behind -> body -> arms -> head -> props in front
  side view           far leg -> far arm (and what it holds) -> body -> near leg -> head -> near arm
Facing left is drawn facing right with the character's LEFT side near (swap) and then mirrored, so
a one-sided thing (a basket, a ladle, a hammer, a bag strap, a pinwheel, a towel) stays on its side.

A character sets:
  maps        HEAD_FRONT / HEAD_BACK (left halves, mirrored), HEAD_SIDE, BODY_FRONT / BODY_BACK, BODY_SIDE
  layout      head_top, body_top, hip, breath_below (rows from here down do not breathe)
  legs        legs = dict(xs, w, mat, shoe, top, skirt) (front view); side legs use the same materials
  arms        front: ARM_R / ARM_L maps (anchor '@' shoulder, '*' hand), shoulders (x of image left / right)
              side: arm_side(c, p, sh, swing, far, left) draws one arm (left: his left arm)
  hooks       behind_front, over_front, behind_side, over_side for props and details
"""

from npc_common import Npc, capsule, stamp, stamp_at


class Villager(Npc):
    LEG = {}
    head_top = 4
    head_top_side = None  # defaults to head_top
    body_top = 22
    hip = 42
    breath_below = 36
    legs = dict(xs=(10, 18), w=4, mat="trousers", shoe="boot", skirt=False)
    shoulders = (6, 25)
    shoulder_y = 25
    side_shoulder = (14, 25)
    side_hip_x = 15

    # -------------------------------------------------------------- front / back
    def legs_front(self, c, p, b, back):
        lg = self.legs
        for (fwd, lift), x0 in ((p.near, lg["xs"][0]), (p.far, lg["xs"][1])):
            down = 1 if fwd > 1 else 0
            y = min(55, 55 - lift + down)
            w = lg["w"]
            left = x0 < 16
            if lg.get("skirt"):
                self.foot_front(c, x0, y, back)
                continue
            c.rect(x0, self.hip + b, x0 + w, y - 4, lg["mat"])
            c.rect(x0, y - 4, x0 + w, y - 4, lg["mat"], 1)
            self.foot_front(c, x0, y, back)
            c.line(x0 + (w - 1 if left else 1), self.hip + 1 + b, x0 + (w - 1 if left else 1), y - 5, lg["mat"], 1)

    def foot_front(self, c, x0, y, back):
        w = self.legs["w"]
        shoe = self.legs["shoe"]
        left = x0 < 16
        c.rect(x0, y - 3, x0 + w, y, shoe)
        c.rect(x0 - (1 if left else 0), y - 1, x0 + w + (0 if left else 1), y, shoe)
        c.line(x0 - (1 if left else 0), y, x0 + w + (0 if left else 1), y, shoe, 1)
        if not back:
            c.put(x0 + 1, y - 3, shoe, 3)
            c.put(x0 + 2, y - 3, shoe, 4)

    def body_shift(self, p, b, up, back):
        def shift(row, col, ch):
            y = self.body_top + row
            return 0, b + (up if y < self.breath_below else 0)
        return shift

    def arms_front(self, c, p, b, up, back):
        xl, xr = self.shoulders
        y = self.shoulder_y + b + up
        # his right arm: image left from the front, image right from behind
        r_swing = max(0, p.arm_near if not back else p.arm_far)
        l_swing = max(0, p.arm_far if not back else p.arm_near)
        if not back:
            self.hand_r = stamp_at(c, self.ARM_R, "@", "*", (xl, y - r_swing * self.swing_r), self.LEG)
            self.hand_l = stamp_at(c, self.ARM_L, "@", "*", (xr, y - l_swing * self.swing_l), self.LEG, flip=True, darker=True)
        else:
            self.hand_r = stamp_at(c, self.ARM_R, "@", "*", (xr, y - r_swing * self.swing_r), self.LEG, flip=True, darker=True)
            self.hand_l = stamp_at(c, self.ARM_L, "@", "*", (xl, y - l_swing * self.swing_l), self.LEG, darker=True)

    swing_r = 1
    swing_l = 1

    def behind_front(self, c, p, b, up, back):
        pass

    def over_front(self, c, p, b, up, back):
        pass

    def front(self, p, back=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        self.legs_front(c, p, b, back)
        self.behind_front(c, p, b, up, back)
        body = self.BODY_BACK if back else self.BODY_FRONT
        if up:  # breathing in lifts the chest: the body underneath fills the row it leaves
            stamp(c, body, 0, self.body_top, self.LEG, mirrored=True, shift=self.body_shift(p, b, 0, back))
        stamp(c, body, 0, self.body_top, self.LEG, mirrored=True, shift=self.body_shift(p, b, up, back))
        self.arms_front(c, p, b, up, back)
        stamp(c, self.HEAD_BACK if back else self.HEAD_FRONT, 0, self.head_top + b + up, self.LEG, mirrored=True)
        if p.blink and not back:
            self.blink_front(c, self.head_top + b + up)
        self.over_front(c, p, b, up, back)
        return c

    def blink_front(self, c, top):
        pass

    # -------------------------------------------------------------- side
    def leg_side(self, c, p, fwd, lift, tone):
        lg = self.legs
        hip = (self.side_hip_x, self.hip + p.bob)
        ax, ay = hip[0] + fwd, 52 - lift
        if not lg.get("skirt"):
            kx, ky = hip[0] + fwd * 0.6 + (1.5 if lift else 0.5), (hip[1] + ay) / 2 - lift * 0.5
            capsule(c, hip[0], hip[1], kx, ky, lg.get("r", 2.2), lg["mat"], tone)
            capsule(c, kx, ky, ax, ay - 1, lg.get("r", 2.2) - 0.2, lg["mat"], tone)
        shoe = lg["shoe"]
        toe = 3 if lift < 2 else 2
        c.rect(int(ax) - 2, ay, int(ax) + toe, ay + 2, shoe, tone)
        c.put(int(ax) + toe + 1, ay + 2 - (1 if lift > 1 else 0), shoe, tone)
        c.line(int(ax) - 2, ay + 3 - (1 if lift > 1 else 0), int(ax) + toe + 1, ay + 3 - (1 if lift > 1 else 0), shoe, 0 if tone == 1 else 1)
        if tone is None:
            c.put(int(ax), ay, shoe, 3)

    def arm_side(self, c, p, sh, swing, far, left):
        """Default: a sleeve to the elbow, the forearm, the hand; forward (+) / back (-)."""
        hx, hy = sh[0] + swing * 1.4, sh[1] + 12
        ex, ey = sh[0] + swing * 0.6, sh[1] + 6
        capsule(c, sh[0], sh[1] + 1, ex, ey, 2.0, self.sleeve, 1 if far else None)
        capsule(c, ex, ey + 1, hx, hy, 1.5, self.forearm, 1 if far else None)
        c.rect(int(hx) - 1, int(hy), int(hx) + 1, int(hy) + 1, "skin", 1 if far else 2)

    sleeve = "shirt"
    forearm = "shirt"
    near_leg_over_body = True

    def behind_side(self, c, p, b, up, swap):
        pass

    def over_side(self, c, p, b, up, swap):
        pass

    def side_body_shift(self, p, b, up):
        def shift(row, col, ch):
            y = self.body_top + row
            return 0, b + (up if y < self.breath_below else 0)
        return shift

    def side(self, p, swap=False):
        c = self.canvas()
        b = p.bob
        up = -p.breath
        sh = (self.side_shoulder[0], self.side_shoulder[1] + b + up)
        self.leg_side(c, p, p.far[0], p.far[1], 1)
        # facing right his right side is near; facing left (swap) his left side is near
        self.arm_side(c, p, sh, p.arm_far, True, left=not swap)
        self.behind_side(c, p, b, up, swap)
        if not self.near_leg_over_body:  # a long apron or skirt hides the thigh
            self.leg_side(c, p, p.near[0], p.near[1], None)
        if up:
            stamp(c, self.BODY_SIDE, 0, self.body_top, self.LEG, shift=self.side_body_shift(p, b, 0))
        stamp(c, self.BODY_SIDE, 0, self.body_top, self.LEG, shift=self.side_body_shift(p, b, up))
        if self.near_leg_over_body:
            self.leg_side(c, p, p.near[0], p.near[1], None)
        top = (self.head_top_side if self.head_top_side is not None else self.head_top) + b + up
        stamp(c, self.HEAD_SIDE, 0, top, self.LEG)
        if p.blink:
            self.blink_side(c, top)
        self.arm_side(c, p, sh, p.arm_near, False, left=swap)
        self.over_side(c, p, b, up, swap)
        return c

    def blink_side(self, c, top):
        pass
