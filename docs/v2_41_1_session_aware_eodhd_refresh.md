# v2.41.1 Session-aware EODHD production refresh

Only exact US 1h 16:00 America/New_York close-marker rows with O=H=L=C and missing volume are excluded from the semantic provider-quality denominator. The semantic non-marker drop limit remains 2%.

The transport threshold is 20% only to allow inspection of quarantined rows before semantic classification. Any non-marker provider failures remain fail-closed. No broker authority or risk setting changes.
