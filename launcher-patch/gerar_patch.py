# -*- coding: utf-8 -*-
"""Gera o catálogo e o patch binário do launcher do reNut (prévia 0.9.0).

Uso (somente leitura no executável de origem):
    .venv\\Scripts\\python -I launcher-patch\\gerar_patch.py --exe <renut.exe> --saida launcher-patch

O catálogo fica em `entradas_launcher.json`. O patch resultante é um JSON com
regiões (offset, bytes antigos, bytes novos). Nada é escrito no executável
original. Além do UTF-8, o gerador aceita literais UTF-16LE (as janelas nativas
do Windows), que o patch 0.8.0 não cobria.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

SECTION_ALIGN = 0x1000
FILE_ALIGN = 0x200
HERE = Path(__file__).resolve().parent


def align_up(v, a):
    return (v + a - 1) // a * a


class PE:
    def __init__(self, data: bytes):
        self.data = data
        self.pe = struct.unpack_from("<I", data, 0x3C)[0]
        self.opt = self.pe + 24
        self.magic = struct.unpack_from("<H", data, self.opt)[0]
        self.image_base = struct.unpack_from("<Q", data, self.opt + 24)[0]
        self.section_align = struct.unpack_from("<I", data, self.opt + 32)[0]
        self.file_align = struct.unpack_from("<I", data, self.opt + 36)[0]
        self.size_of_image = struct.unpack_from("<I", data, self.opt + 56)[0]
        self.checksum_off = self.opt + 64
        self.nsec = struct.unpack_from("<H", data, self.pe + 6)[0]
        self.opt_size = struct.unpack_from("<H", data, self.pe + 20)[0]
        self.sec_tab = self.opt + self.opt_size
        self.sections = []
        for i in range(self.nsec):
            off = self.sec_tab + 40 * i
            name = data[off:off + 8].rstrip(b"\0").decode("latin-1")
            vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
            chars = struct.unpack_from("<I", data, off + 36)[0]
            self.sections.append({"name": name, "vsize": vsize, "vaddr": vaddr,
                                  "rsize": rsize, "raw": roff, "chars": chars,
                                  "header": off})
        self.relocs = self._relocs()

    def _relocs(self):
        out = set()
        sec = next((s for s in self.sections if s["name"] == ".reloc"), None)
        if not sec:
            return out
        d = self.data[sec["raw"]:sec["raw"] + sec["rsize"]]
        i = 0
        while i + 8 <= len(d):
            page, size = struct.unpack_from("<II", d, i)
            if size < 8:
                break
            for j in range(8, size, 2):
                ent = struct.unpack_from("<H", d, i + j)[0]
                typ, off = ent >> 12, ent & 0xFFF
                if typ == 10:
                    out.add(page + off)
            i += size
        return out

    def off_to_rva(self, off):
        for s in self.sections:
            if s["raw"] <= off < s["raw"] + s["rsize"]:
                return s["vaddr"] + (off - s["raw"])
        return None

    def rva_to_off(self, rva):
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["rsize"], s["vsize"]):
                return s["raw"] + (rva - s["vaddr"])
        return None


def load_entries(path: Path):
    entries = json.loads(path.read_text(encoding="utf-8"))
    for e in entries:
        e.setdefault("encoding", "utf-8")
        e.setdefault("file", "renut.exe")
    return entries


def encode(text: str, encoding: str) -> bytes:
    return text.encode("utf-16le" if encoding == "utf-16le" else "utf-8")


def pad_with(text: bytes, total: int, encoding: str) -> bytes:
    room = total - len(text)
    if room <= 0:
        return text
    fill = b"\x20\x00" if encoding == "utf-16le" else b"\x20"
    return text + fill * (room // len(fill))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--entradas", default=str(HERE / "entradas_launcher.json"))
    args = ap.parse_args()
    exe = Path(args.exe)
    outdir = Path(args.saida)
    data = exe.read_bytes()
    pe = PE(data)
    sha = hashlib.sha256(data).hexdigest()

    text = next(s for s in pe.sections if s["name"] == ".text")
    code = data[text["raw"]:text["raw"] + text["rsize"]]
    code_rva = text["vaddr"]

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    rip_refs = defaultdict(list)
    imm_sites = []
    for insn in md.disasm(code, code_rva):
        for op in insn.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                target = insn.address + insn.size + op.mem.disp
                rip_refs[target].append({"addr": insn.address, "insn": insn.mnemonic,
                                         "disp_off": insn.size - 4, "len": insn.size})
            elif op.type == X86_OP_IMM:
                val = op.imm & 0xFFFFFFFFFFFFFFFF
                if insn.mnemonic.startswith(("j", "call", "loop")):
                    continue
                for size in (1, 2, 4, 8):
                    if size == 8:
                        if insn.mnemonic not in ("mov", "movabs"):
                            continue
                        raw = val.to_bytes(8, "little")
                    else:
                        if val > (1 << (size * 8)) - 1:
                            continue
                        raw = (val & ((1 << (size * 8)) - 1)).to_bytes(size, "little")
                    if not raw or raw == b"\0" * size:
                        continue
                    pos = -1
                    for k in range(len(insn.bytes) - size, -1, -1):
                        if insn.bytes[k:k + size] == raw:
                            pos = k
                            break
                    if pos < 0:
                        continue
                    imm_sites.append({"addr": insn.address, "size": size, "raw": raw,
                                      "file_off": pe.rva_to_off(insn.address + pos),
                                      "insn": insn.mnemonic})

    imm_by_bytes = defaultdict(list)
    for s in imm_sites:
        imm_by_bytes[s["raw"]].append(s)

    entries_out = []
    edits = []          # (offset, old, new, note, prio)
    reloc = []          # (entry, new_text_bytes)
    imm_claims = {}

    def add_edit(off, old, new, note, prio=0):
        assert len(old) == len(new), (note, len(old), len(new))
        if old != new:
            edits.append({"offset": off, "old": old, "new": new, "note": note, "prio": prio})

    for e in load_entries(Path(args.entradas)):
        if e["file"] != "renut.exe":
            continue
        eid = e["id"]
        enc = e["encoding"]
        nb = encode(e["en"], enc)
        pb = encode(e["pt"], enc)
        manual = e.get("code_edits", [])
        if manual:
            for ce in manual:
                add_edit(ce["offset"], base64.b64decode(ce["old"]), base64.b64decode(ce["new"]),
                         f"{eid}: imediato de código", 20000)
            entries_out.append({
                "id": eid, "en": e["en"], "pt": e["pt"], "category": e["category"],
                "context": e["context"], "screen": e.get("screen", e["context"]),
                "condition": e.get("condition", ""), "source": e["source"],
                "encoding": enc, "file": e["file"],
                "en_bytes": len(nb), "pt_bytes": len(pb), "mode": "code_immediate",
                "status": "traduzida por imediato de código",
                "occurrences": [{"offset": ce["offset"], "rva": None, "standalone": False} for ce in manual],
                "refs": [], "immediates": [],
            })
            continue
        term = b"\0\0" if enc == "utf-16le" else b"\0"
        occ = []
        start = 0
        allowed = e.get("offsets")
        while True:
            off = data.find(nb, start)
            if off < 0:
                break
            start = off + 1
            r = pe.off_to_rva(off)
            if r is None:
                continue
            after = data[off + len(nb): off + len(nb) + len(term)]
            before = data[off - len(term):off] if off else term
            if after != term:
                continue
            if allowed is not None and off not in allowed:
                continue
            occ.append({"off": off, "rva": r, "standalone": before == term})
        refs = []
        for o in occ:
            for x in rip_refs.get(o["rva"], []):
                refs.append({"kind": "rip", "off": o["off"], **x})
            va = pe.image_base + o["rva"]
            p = 0
            while True:
                q = data.find(struct.pack("<Q", va), p)
                if q < 0:
                    break
                p = q + 1
                refs.append({"kind": "ptr", "off": o["off"], "file_off": q,
                             "reloc": pe.off_to_rva(q) in pe.relocs})
        if e.get("ref_addrs") is not None:
            refs = [r for r in refs if r.get("addr") in e["ref_addrs"]]
        imms = []
        if enc == "utf-8":
            for i in range(len(nb)):
                for size in (8, 4, 2):
                    if i + size > len(nb):
                        continue
                    raw = nb[i:i + size]
                    if len(raw) < 2 or raw == b"\0" * size:
                        continue
                    for s in imm_by_bytes.get(raw, []):
                        imms.append({"window": i, "size": size, **s})
            seen = set()
            uniq = []
            for x in imms:
                k = (x["file_off"], x["window"], x["size"])
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(x)
            imms = uniq

            def find_clusters(nb, sites):
                found = {}
                for anchor in sites:
                    if anchor["size"] < 4 or anchor["window"] not in (0, len(nb) - anchor["size"]):
                        continue
                    chosen = {anchor["file_off"]: anchor}
                    covered = [(anchor["window"], anchor["window"] + anchor["size"])]
                    ordered = sorted(sites, key=lambda x: abs(x["addr"] - anchor["addr"]))
                    for cand in ordered:
                        if abs(cand["addr"] - anchor["addr"]) > 96:
                            break
                        if cand["file_off"] in chosen:
                            continue
                        cs, ce = cand["window"], cand["window"] + cand["size"]
                        if cs < 0 or ce > len(nb):
                            continue
                        if any(cs == a and ce == b for a, b in covered):
                            continue
                        if any(cs <= b and a <= ce for a, b in covered):
                            chosen[cand["file_off"]] = cand
                            covered.append((cs, ce))
                            merged = []
                            for a, b in sorted(covered):
                                if merged and a <= merged[-1][1]:
                                    merged[-1] = (merged[-1][0], max(merged[-1][1], b))
                                else:
                                    merged.append((a, b))
                            covered = merged
                        if covered == [(0, len(nb))]:
                            break
                    if covered == [(0, len(nb))]:
                        found.update(chosen)
                return list(found.values())

            imms = find_clusters(nb, imms)

        fits = len(pb) <= len(nb)
        has_imm = bool(imms)
        safe_refs = refs and all((r["kind"] == "ptr" and r["reloc"]) or r["kind"] == "rip" for r in refs)
        if not occ and not imms:
            mode = "not_found"
        elif fits:
            mode = "in_place"
        elif safe_refs and not has_imm:
            mode = "relocate"
        else:
            mode = "blocked"

        entry = {
            "id": eid, "en": e["en"], "pt": e["pt"], "category": e["category"],
            "context": e["context"], "screen": e.get("screen", e["context"]),
            "condition": e.get("condition", ""), "source": e["source"],
            "encoding": enc, "file": e["file"],
            "en_bytes": len(nb), "pt_bytes": len(pb), "mode": mode,
            "status": {"in_place": "traduzida no mesmo espaço", "relocate": "traduzida e realocada",
                       "blocked": "bloqueada", "not_found": "ausente do binário"}[mode],
            "occurrences": [{"offset": o["off"], "rva": o["rva"], "standalone": o["standalone"]} for o in occ],
            "refs": [{"kind": r["kind"], "file_off": r.get("file_off"), "addr": r.get("addr")} for r in refs],
            "immediates": [{"file_off": x["file_off"], "window": x["window"], "size": x["size"]} for x in imms],
        }
        entries_out.append(entry)

        if mode == "in_place":
            padded = pad_with(pb, len(nb), enc)
            for o in occ:
                add_edit(o["off"], nb, padded, f"{eid}: literal", len(nb))
            for x in imms:
                win, size = x["window"], x["size"]
                new = padded[win:win + size]
                old = data[x["file_off"]:x["file_off"] + size]
                if old != new and len(new) == size and all(32 <= c < 127 for c in old):
                    claim = imm_claims.get(x["file_off"])
                    if claim is None or len(nb) > claim[0]:
                        imm_claims[x["file_off"]] = (len(nb), new, f"{eid}: imediato")
        elif mode == "relocate":
            reloc.append((entry, pb))
            for r in refs:
                if r["kind"] == "ptr":
                    old = data[r["file_off"]:r["file_off"] + 8]
                    reloc.append((entry, pb, "ptr", r["file_off"], old))
                elif r["kind"] == "rip":
                    reloc.append((entry, pb, "rip", r["addr"], r))

    for off, (_, new, note) in sorted(imm_claims.items()):
        old = data[off:off + len(new)]
        add_edit(off, old, new, note, 1)
    reloc_entries = [r for r in reloc if len(r) == 2]
    section_edits = []
    if reloc_entries:
        blob = bytearray()
        new_rvas = {}
        for entry, pb in reloc_entries:
            while len(blob) % 16:
                blob.append(0)
            new_rvas[entry["id"]] = len(blob)
            blob += pb + (b"\0\0" if entry["encoding"] == "utf-16le" else b"\0")
        last = max(pe.sections, key=lambda s: s["vaddr"])
        new_rva = align_up(last["vaddr"] + max(last["vsize"], last["rsize"]), SECTION_ALIGN)
        new_raw = align_up(len(data), FILE_ALIGN)
        vsize = len(blob)
        rsize = align_up(vsize, FILE_ALIGN)
        header_off = pe.sec_tab + 40 * pe.nsec
        name = b".ptbr\0\0\0"
        header = name + struct.pack("<IIII", vsize, new_rva, rsize, new_raw) + b"\0" * 12
        header += struct.pack("<I", 0x40000040)
        section_edits.append({"offset": header_off, "old": data[header_off:header_off + 40],
                              "new": header, "note": "novo cabeçalho .ptbr", "prio": 10000})
        nsec_off = pe.pe + 6
        section_edits.append({"offset": nsec_off, "old": data[nsec_off:nsec_off + 2],
                              "new": struct.pack("<H", pe.nsec + 1), "note": "NumberOfSections", "prio": 10000})
        size_img = align_up(new_rva + vsize, SECTION_ALIGN)
        section_edits.append({"offset": pe.opt + 56, "old": data[pe.opt + 56:pe.opt + 60],
                              "new": struct.pack("<I", size_img), "note": "SizeOfImage", "prio": 10000})
        pad = new_raw - len(data)
        body = b"\0" * pad + bytes(blob) + b"\0" * (rsize - vsize)
        section_edits.append({"offset": len(data), "old": b"", "new": body, "note": "seção .ptbr", "prio": 10000})
        for r in reloc:
            if len(r) == 2:
                continue
            entry, pb, kind, where, extra = r
            target_rva = new_rva + new_rvas[entry["id"]]
            if kind == "ptr":
                section_edits.append({"offset": where, "old": extra,
                                      "new": struct.pack("<Q", pe.image_base + target_rva),
                                      "note": f"{entry['id']}: ponteiro", "prio": 10000})
            else:
                insn_off = pe.rva_to_off(extra["addr"])
                disp_off = insn_off + extra["disp_off"]
                old = data[disp_off:disp_off + 4]
                new_disp = target_rva - (extra["addr"] + extra["len"])
                section_edits.append({"offset": disp_off, "old": old,
                                      "new": struct.pack("<i", new_disp),
                                      "note": f"{entry['id']}: rip", "prio": 10000})
        edits.extend(section_edits)

    accepted = []
    for e in sorted(edits, key=lambda e: (-e["prio"], e["offset"])):
        end = e["offset"] + len(e["old"])
        if any(e["offset"] < a["offset"] + len(a["old"]) and a["offset"] < end for a in accepted):
            continue
        accepted.append(e)
    edits = accepted
    edits.sort(key=lambda e: e["offset"])
    for a, b in zip(edits, edits[1:]):
        if a["offset"] + len(a["old"]) > b["offset"]:
            raise SystemExit(f"sobreposição: {a['note']} e {b['note']}")

    out = bytearray(data)
    for e in edits:
        off = e["offset"]
        old = e["old"]
        if old and bytes(out[off:off + len(old)]) != old:
            raise SystemExit(f"bytes antigos não conferem em {off:#x} ({e['note']})")
        out[off:off + len(e["new"])] = e["new"]
    if section_edits:
        csum_off = pe.checksum_off
        out[csum_off:csum_off + 4] = b"\0\0\0\0"
        total = 0
        for i in range(0, len(out), 2):
            w = out[i] | ((out[i + 1] << 8) if i + 1 < len(out) else 0)
            total += w
            total = (total & 0xFFFF) + (total >> 16)
        total = (total & 0xFFFF) + (total >> 16)
        out[csum_off:csum_off + 4] = struct.pack("<I", total)
        edits.append({"offset": csum_off, "old": data[csum_off:csum_off + 4],
                      "new": bytes(out[csum_off:csum_off + 4]), "note": "checksum PE", "prio": 10000})
        edits.sort(key=lambda e: e["offset"])

    out_hash = hashlib.sha256(bytes(out)).hexdigest()

    patch = {
        "schema": "renut-launcher-patch/1",
        "launcher": {"release": "big-lua-energy", "version": "0.11.21",
                     "input_size": len(data), "input_sha256": sha,
                     "output_size": len(out), "output_sha256": out_hash},
        "edits": [{"offset": e["offset"], "old": base64.b64encode(e["old"]).decode("ascii"),
                   "new": base64.b64encode(e["new"]).decode("ascii"), "note": e["note"]}
                  for e in edits],
    }
    modes = Counter(e["mode"] for e in entries_out)
    catalog = {
        "schema": "renut-launcher-catalog/2",
        "launcher": patch["launcher"],
        "generated_from": Path(args.entradas).name,
        "totals": {
            "entries": len(entries_out),
            "in_place": modes["in_place"],
            "relocated": modes["relocate"],
            "blocked": modes["blocked"],
            "not_found": modes["not_found"],
            "code_immediate": modes["code_immediate"],
            "utf16": sum(1 for e in entries_out if e["encoding"] == "utf-16le"),
            "by_category": dict(Counter(e["category"] for e in entries_out)),
        },
        "entries": entries_out,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "catalogo.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1),
                                          encoding="utf-8", newline="\n")
    (outdir / "renut_launcher_ptbr.patch").write_text(json.dumps(patch, ensure_ascii=False, indent=1),
                                                      encoding="utf-8", newline="\n")
    (outdir / "manifesto.json").write_text(json.dumps({
        "schema": "renut-launcher-manifest/2",
        "patch_version": "0.9.0-preview.1",
        "status": "preview",
        "release": "big-lua-energy",
        "version": "0.11.21",
        "input_size": len(data),
        "input_sha256": sha,
        "output_size": len(out),
        "output_sha256": out_hash,
        "patch_file": "renut_launcher_ptbr.patch",
        "catalog_file": "catalogo.json",
        "entries": len(entries_out),
        "edits": len(edits),
        "in_place": modes["in_place"],
        "relocated": modes["relocate"],
        "blocked": modes["blocked"],
        "not_found": modes["not_found"],
        "engine_manifest": "engine/manifesto.json",
        "game_mod_sha256": "7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25",
        "game_mod_version": "0.7.0",
    }, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"entradas: {len(entries_out)}  in-place: {modes['in_place']}  "
          f"relocadas: {modes['relocate']}  bloqueadas: {modes['blocked']}  "
          f"ausentes: {modes['not_found']}  utf16: {catalog['totals']['utf16']}")
    print(f"edições: {len(edits)}  saída: {len(out)} bytes  sha256: {out_hash}")
    for e in entries_out:
        if e["mode"] in ("blocked", "not_found"):
            print(e["mode"].upper(), e["id"], e["en_bytes"], e["pt_bytes"],
                  len(e["refs"]), len(e["immediates"]))


if __name__ == "__main__":
    main()