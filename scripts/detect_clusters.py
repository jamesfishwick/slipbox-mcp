#!/usr/bin/env python3
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from slipbox_mcp.services import build_services


def main():
    print("Starting cluster detection...")
    cluster_service = build_services().cluster
    report = cluster_service.refresh_report()

    print(f"Report saved to: {cluster_service.report_path}")
    print(f"Total notes: {report.stats['total_notes']}")
    print(f"Orphaned notes: {report.stats['total_orphans']}")
    print(f"Clusters needing structure: {report.stats['clusters_needing_structure']}")

    if report.clusters:
        print("\nTop clusters:")
        for c in report.clusters[:5]:
            print(f"  {c.score:.2f} | {c.suggested_title} ({c.note_count} notes)")


if __name__ == "__main__":
    main()
