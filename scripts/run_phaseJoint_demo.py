import argparse
import sys
import time
import numpy as np

from g1_playground.dds import create_dds_topic_to_communicate_with_g1
from g1_playground.robot import UnitreeG1Robot, G129DofJointIndex
from g1_playground.policies.ankle_swing import AnkleSwingPolicy
from g1_playground.policies.movement_testing_tools import JointTunerPolicy, PhaseTestPolicy

def main():
    parser = argparse.ArgumentParser(description="Run the atesetr for the joints, and debug demo policy on the G1 robot.")
    parser.add_argument("--network_interface", default=None,
                        help="Network interface for real robot or MuJoCo sim (e.g. enp2s0, lo)")
    parser.add_argument("--dds_channel_id", type=int, default=1,
                        help="DDS domain channel ID (default: 1 for sim, use 0 for real robot)")
    args = parser.parse_args()

    print("WARNING: Please ensure there are no obstacles around the robot while running this example.")
    try:
        input("Press Enter to continue...")
    except KeyboardInterrupt:
        print("\nAborted before start.")
        return

    create_dds_topic_to_communicate_with_g1(args.dds_channel_id, args.network_interface)

    extender = [
    -0.0002715712762437761,
    -0.003813965478911996,
    -0.005133028607815504,
    -0.012610559351742268,
    0.03110571764409542,
    8.189560321625322e-05,
    0.0003864132449962199,
    0.002948490669950843,
    0.005797702353447676,
    -0.012028425931930542,
    0.031136266887187958,
    -8.770319982431829e-05,
    0.0002529710181988776,
    0.001415475970134139,
    -0.037286706268787384,
    -0.41499248147010803,
    0.01575571671128273,
    0.012101489119231701,
    0.28154101967811584,
    1.4689756631851196,
    -0.019146952778100967,
    -0.051459409296512604,
    -0.03946563974022865,
    -0.020087722688913345,
    -0.010721316561102867,
    1.2697832584381104,
    0.007655221037566662,
    -0.014329438097774982,
    0.04171999543905258
  ]
    policy = PhaseTestPolicy(extender)
    robot = UnitreeG1Robot(policy=policy)

    try:
        robot.initialize()
        robot.start()
        print("Running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        robot.stop()
        print("Robot stopped. Exiting.")


if __name__ == "__main__":
    main()
    sys.exit(0)