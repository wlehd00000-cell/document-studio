"""Validate a Company Pack and report approval readiness."""
import argparse
import json
from pathlib import Path
from company_pack import CompanyPackError, load_company_pack, validate_company_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()
    try:
        pack = load_company_pack(args.pack)
        issues = validate_company_pack(pack)
        ok = not issues or not args.require_approved
        result = {"valid": ok, "pack_id": pack.pack_id, "version": pack.version,
                  "lineage": list(pack.lineage), "issues": [vars(x) for x in issues]}
    except CompanyPackError as exc:
        ok = False
        result = {"valid": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
