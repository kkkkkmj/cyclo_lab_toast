# Task behavior and success criteria

The v2 configuration and control/physics values are copied from the latest working tree:

- Four-groove rack, native 230 × 130 × 45mm, 60mm groove pitch. Dynamic rack/bread settling remains unresolved.
- Lever starts a loaded cycle on entry to **90%** travel. This differs intentionally from the shared lever-pressed predicate (85%); values were not unified.
- Heating begins after lowering reaches its measured position/velocity condition, then lasts **4 simulation seconds**. Per-ID presence throughout heating determines eligibility; removal/reinsertion invalidates that slice for the cycle. The phase drives LED behavior.
- Carriage rising target and upper limit are **+35mm**; lower travel is −45mm.
- v2 gripper master/slave gains are **100/4**; master velocity limit is **6.5rad/s**, slave velocity limits remain authored in the robot USD. Arm and lift settings are unchanged; see [configuration audit](../docs/release/PROVENANCE.md).
- Success needs completed pop-up, released lever, and **at least one identical bread ID both heated and placed on the plate**. Plate-local bread geometry-center XY distance must be **<0.04m; exactly 40mm fails**. For that same slice, every support vertex must have plate-local height strictly between −0.002m and 0.050m, the absolute relative rotation matrix element `R[2,2]` must be >0.94, and world linear speed must be <0.15m/s. The plate must have world `R[2,2]` >0.985, XY displacement from its default position <0.025m, and environment-local X >0.419m. There is no separate bread angular-speed or plate-speed check.
- Pop-up completion is latched as `phase == 4` after rising for at least 0.92 simulation seconds with carriage position within 0.0015m of the +0.035m target; the transition does not check carriage speed. “Released lever” means press ratio <0.85, not necessarily fully open. See [success predicates](../source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/config/ffw_bg2/bimanual_mdp.py) and [cycle transitions](../source/cyclo_lab/cyclo_lab/manager_based/manipulation/make_toast/config/ffw_bg2/toast_cycle.py).
- Serving v2 no longer requires arms at standby, gripper angles below the old threshold, lift return, or reserve slices on the rack. Earlier non-serving tasks retain their distinct conditions.

These predicates describe Serving v2. See [episode result policy](../scripts/quest_diagnostic/EPISODE_RESULTS.md) for how termination outcomes become recording labels.

[Documentation index](README.md)
