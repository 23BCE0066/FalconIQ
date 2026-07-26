"""
Lightweight pure-Python PDF generator for AML Compliance Reports.
Produces standard PDF 1.4 output without external library dependencies.
"""
import textwrap

def make_simple_pdf(text: str) -> bytes:
    """Converts plain text / markdown into a basic valid PDF file."""
    lines = []
    for raw_line in text.splitlines():
        # Strip or replace unsupported non-ASCII characters for basic PDF fonts
        clean_line = raw_line.encode("latin1", "replace").decode("latin1")
        # Wrap long lines to fit on standard 595pt width page with margins
        wrapped = textwrap.wrap(clean_line, width=80)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)

    page_commands = []
    current_page = []
    y = 780

    for line in lines:
        if y < 50:
            page_commands.append(current_page)
            current_page = []
            y = 780
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        current_page.append(f"BT /F1 10 Tf 40 {y} Td ({escaped}) Tj ET")
        y -= 14

    if current_page or not page_commands:
        page_commands.append(current_page)

    objects = []
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    page_ids = []
    next_id = 4
    for _ in range(len(page_commands)):
        page_ids.append(next_id)
        next_id += 2

    kids_str = " ".join([f"{pid} 0 R" for pid in page_ids])
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(page_commands)} >>\nendobj\n")
    objects.append("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

    for i, cmds in enumerate(page_commands):
        pid = 4 + i * 2
        cid = pid + 1
        stream_data = "\n".join(cmds)
        objects.append(f"{pid} 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> /MediaBox [0 0 595 842] /Contents {cid} 0 R >>\nendobj\n")
        objects.append(f"{cid} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n{stream_data}\nendstream\nendobj\n")

    output = ["%PDF-1.4\n"]
    offsets = [0]
    curr_off = len(output[0])
    for obj in objects:
        offsets.append(curr_off)
        output.append(obj)
        curr_off += len(obj)

    xref_off = curr_off
    xref = [f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n")
    output.extend(xref)
    output.append(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_off}\n%%EOF\n")
    
    return "".join(output).encode("latin1")
