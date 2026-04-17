#!/usr/bin/env python3
import argparse
import sys
from typing import Dict, List
from src.topology import getCacheTopology, getCoresForCacheLevel, getNumaTopology
from src.pinner import (
    pinToCacheLevel,
    getCurrentProcessAffinity,
    suggestOptimization,
    unpinProcessFromCacheLevel,
)

def showUserTheirTopologies(args):
    cacheTopology: Dict[str, Dict[int, List[int]]]  = getCacheTopology();
    print(f"[# - Your cache topology - #]");

    for cacheLevelKey in ["L1", "L2", "L3"]:
        if cacheLevelKey in cacheTopology:
            print(f"\n{cacheLevelKey}:");
            for domainId, CPUs in cacheTopology[cacheLevelKey].items():
                print(f"  Domain {domainId}: cores {CPUs}");

    if args.numa:
        NUMA_TOPOLOGY: Dict[int, List[int]] = getNumaTopology()
        print("\n[# - Your NUMA topology - #]");
        for nodeId, CPUs in sorted(NUMA_TOPOLOGY.items()):
            print(f"  Node {nodeId}: cores {CPUs}");

def commandPin(args):
    if not args.pid:
        print("[ERROR]: --pid (process ID) is required")
        sys.exit(1);

    if args.level:
        processSuccessStatus: bool = pinToCacheLevel(args.pid, args.level);
        sys.exit(0 if (processSuccessStatus == 0 or processSuccessStatus) else 1);

    if args.core:
        from src.pinner import pinProcessToCacheLevel;

        processSuccessStatus: bool = pinProcessToCacheLevel(args.pid, [args.core]);
        sys.exit(0 if (processSuccessStatus == 0 or processSuccessStatus) else 1);

    print("[ERROR]: specify --level or --core");
    sys.exit(1);

def commandSuggest(args):
    if not args.pid:
        print("[ERROR]: --pid (process ID) is required")
        sys.exit(1)

    currentAffinityCores: List[int] = getCurrentProcessAffinity(args.pid);

    if currentAffinityCores is None:
        print(f"[ERROR]: could not get affinity for PID {args.pid}");
        sys.exit(1);

    print(f"Current PID affinity: cores {currentAffinityCores}");
    if args.verbose:
        result: Dict | None = suggestOptimization(args.pid);
        if result:
            print(f"\nSuggestions:");
            for aSuggestion in result["suggestions"]:
                status = "OPTIMAL" if aSuggestion["optimal"] else "SUBOPTIMAL";
                print(f"  {aSuggestion['level']}: {aSuggestion['cores']} ({status})")

def main():
    parser = argparse.ArgumentParser(
        description="CPU Affinity Pinning with cool Cache Topology Awareness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py show                # show ONLY cache topology
  python main.py show --numa         # show BOTH cache + NUMA topology
  python main.py pin 67 --level L2   # pin PID to the L2 cache domain
  python main.py pin 67 --core 7     # pin an unpinned PID to a specific core
  python main.py unpin 67            # unpin a PID from a previously pinned core (it will use all cores)
  python main.py suggest 67          # will suggest you the optimal cores to pin the PID to
  python main.py suggest 67 -v       # verbose suggestions for nerds
        """,
    );

    subparsers = parser.add_subparsers(dest="command", required=True);
    showParser = subparsers.add_parser("show", help="Show cache topology");
    showParser.add_argument("--numa", action="store_true", help="include NUMA topology");

    pinParser = subparsers.add_parser("pin", help="pin process to cache level or core");
    pinParser.add_argument("--pid", type=int, required=True, help="process ID");
    pinParser.add_argument("--level", help="cache level (L1, L2, L3)");
    pinParser.add_argument("--core", type=int, help="specific core");

    suggestParser = subparsers.add_parser("suggest", help="suggest optimal cores");
    suggestParser.add_argument("--pid", type=int, required=True, help="process ID");
    suggestParser.add_argument("-v", "--verbose", action="store_true", help="verbose output");

    unpinParser = subparsers.add_parser("unpin", help="unpin process (reset to all cores)");
    unpinParser.add_argument("--pid", type=int, required=True, help="process ID")

    parsedArgs = parser.parse_args();

    if parsedArgs.command == "show":
        showUserTheirTopologies(parsedArgs);
    elif parsedArgs.command == "pin":
        commandPin(parsedArgs);
    elif parsedArgs.command == "suggest":
        commandSuggest(parsedArgs);
    elif parsedArgs.command == "unpin":
        success = unpinProcessFromCacheLevel(parsedArgs.pid)
        sys.exit(0 if success else 1);


if __name__ == "__main__":
    main();
