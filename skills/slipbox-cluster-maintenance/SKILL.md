---
name: slipbox-cluster-maintenance
description: "Use at the start of a slipbox session to surface pending housekeeping — knowledge clusters grown large enough to need a structure note. Trigger on: any slipbox maintenance, what needs attention in my slipbox, check my clusters, start-of-session housekeeping."
---

<!-- Generated from src/slipbox_mcp/server/descriptions.py by scripts/build_skills.py. Do not edit by hand. -->

# Cluster Maintenance

Surface pending Zettelkasten housekeeping, grounded in the actual slipbox.

1. Load the current cluster analysis with `slipbox_get_cluster_report`. If it looks stale, run `slipbox_refresh_clusters` first.
2. Report the top clusters that lack a structure note, ranked by urgency score (note count, orphan ratio, link density, recency).
3. For each, show its suggested title, note/orphan counts, score, and ID.
4. Offer to: create a structure note for one (`slipbox_create_structure_from_cluster`), show more detail, skip for now, or dismiss permanently (`slipbox_dismiss_cluster`).

If no clusters need attention, say so — the slipbox is well-organized.
