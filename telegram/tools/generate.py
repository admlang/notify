#!/usr/bin/env python3
"""Generate the typed Bot API layer of adm.notify.telegram from the Bot API
reference (https://core.telegram.org/bots/api).

Usage: python3 tools/generate.py <api.html> <library folder>

Writes types.adm (every object of the API), methods.adm (a Bot method per
API method) and methods_test.adm (a call of every method against the test
server). The rest of the library (the client, uploads, keyboards,
updates, the webhook handler) is written by hand.
"""
import html
import re
import sys

KEYWORDS = set("""application library plugin module check view style component datatype
service type union interface enum struct partial internal let const def use atomic weak
async cuda sql infix meta return fail expects provides begin rollback transaction defer
yield try onerror await if else when unless as is in for forall every empty break finish
switch match select where case continue default assert self none true false""".split())

# Names the hand-written part of the library declares.
HAND_WRITTEN = {"InputFile"}

PRIMITIVES = {
    "Integer": "int",
    "Int": "int",
    "Float": "float",
    "Float number": "float",
    "String": "string",
    "Boolean": "bool",
    "True": "bool",
}


def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def camel(name):
    parts = name.split("_")
    out = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    if out == "type":
        return "kind"
    if out in KEYWORDS:
        return out + "Value"
    return out


def first_sentence(text):
    text = " ".join(text.split())
    # Whether a field is optional shows in its type; the sentence after says
    # what it is.
    if text.startswith("Optional. "):
        text = text[len("Optional. "):]
    match = re.match(r"(.+?\.)(\s|$)", text)
    sentence = match.group(1) if match else text
    return sentence.replace("*/", "* /")


def comment(text, indent):
    words = first_sentence(text).split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + 1 > 90 - len(indent):
            lines.append(line)
            line = word
        else:
            line = word if not line else line + " " + word
    if line:
        lines.append(line)
    return "".join(f"{indent}// {l}\n" for l in lines)


def parse(document):
    """The types and methods of the reference, in its order."""
    types, methods, abstract = [], [], {}
    parts = re.split(r'<h4><a class="anchor" name="([a-z0-9_]+)"[^>]*>', document)
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        title = re.search(r"</a>([^<]+)</h4>", body)
        if not title:
            continue
        name = title.group(1).strip()
        if " " in name:
            continue
        # The section ends at the next heading.
        section = re.split(r"<h[34]>", body, maxsplit=1)[0]
        paragraphs = re.findall(r"<p>(.*?)</p>", section, re.S)
        description = text_of(" ".join(paragraphs))
        raw_description = " ".join(paragraphs)
        table = re.search(r"<table.*?</table>", section, re.S)
        rows = []
        if table:
            for tr in re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S)[1:]:
                cells = re.findall(r"<td>(.*?)</td>", tr, re.S)
                rows.append(cells)
        if name[0].isupper():
            variants = []
            listing = re.search(r"<ul>(.*?)</ul>", section, re.S)
            if not table and listing:
                # A type without fields whose section lists other types is a
                # union of them.
                variants = [v for v in re.findall(r'<a href="#([a-z0-9_]+)">([A-Z][A-Za-z]+)</a>', listing.group(1)) if v[1] != name]
                if variants:
                    abstract[name] = [v[1] for v in variants]
            types.append({"name": name, "description": description, "rows": rows, "variants": [v[1] for v in variants]})
        elif name[0].islower():
            methods.append({"name": name, "description": description, "raw": raw_description, "rows": rows})
    return types, methods, abstract


def adm_type(api, known, abstract, for_param=False):
    api = api.strip()
    if api.startswith("Array of "):
        inner = adm_type(api[len("Array of "):], known, abstract, for_param)
        return inner + "[]"
    if " or " in api or " and " in api:
        return "any"
    if api in PRIMITIVES:
        return PRIMITIVES[api]
    if api == "InputFile":
        return "InputFile"
    if api in abstract:
        return "any" if for_param else api
    if api in known:
        return api
    return "any"


# Methods the hand-written part covers: getUpdates is what `Bot.updates()`
# streams.
HAND_WRITTEN_METHODS = {"getUpdates"}


def method_name(api):
    """The ADM name of an API method: without the `get` prefix ADM names do
    not carry (getChatMember is chatMember)."""
    if api.startswith("get") and api[3:4].isupper():
        return api[3].lower() + api[4:]
    return api


def zero_of(adm):
    return {"int": "0", "float": "0.0", "string": '""', "bool": "false"}.get(adm)


def write_types(types, abstract, folder):
    known = {t["name"] for t in types} | HAND_WRITTEN
    out = ["// Generated by tools/generate.py from the Bot API reference; do not edit.\n",
           "partial module adm.notify.telegram {\n",
           "\tuse std.data.encoding\n"]
    fields_of = {t["name"]: t["rows"] for t in types}
    for t in types:
        name = t["name"]
        if name in HAND_WRITTEN:
            continue
        rows = t["rows"]
        variants = t["variants"]
        merged = []
        if variants:
            seen = set()
            for variant in variants:
                for row in fields_of.get(variant, []):
                    field = text_of(row[0])
                    if field in seen:
                        continue
                    seen.add(field)
                    merged.append((row[0], row[1], "Optional. " + text_of(row[2])))
            rows = merged
        if not rows and not variants:
            # An object without fields (a placeholder of the API).
            out.append("\n" + comment(t["description"] or name, "\t"))
            out.append(f"\tstruct {name} {{\n\t\t@json(omitempty = true)\n\t\tunused bool\n\t}}\n")
            continue
        out.append("\n" + comment(t["description"] or name, "\t"))
        if variants:
            out.append(f"\t// One struct holds the fields of every kind: {', '.join(variants)}.\n")
        out.append(f"\tstruct {name} {{\n")
        for row in rows:
            field = text_of(row[0])
            api = text_of(row[1])
            description = text_of(row[2]) if len(row) > 2 else ""
            optional = description.startswith("Optional") or bool(variants)
            adm = adm_type(api, known, abstract)
            if adm == "string" and "attach://" in description:
                # A field the API types as a String that also takes an upload
                # by its `attach://` name: an InputFile, or the text itself.
                adm = "any"
            if optional and adm not in ("int", "float", "string", "bool") and not adm.endswith("[]"):
                adm = "?" + adm
            local = camel(field)
            out.append(comment(description, "\t\t"))
            options = []
            if local != field:
                options.append(f'"{field}"')
            if optional:
                options.append("omitempty = true")
            if options:
                out.append(f"\t\t@json({', '.join(options)})\n")
            default = " = none" if adm.startswith("?") or adm == "any" else ""
            out.append(f"\t\t{local} {adm}{default}\n")
        out.append("\t}\n")
    out.append("}\n")
    open(f"{folder}/types.adm", "w").write("".join(out))


def return_type(method, known, abstract):
    raw = method["raw"]
    sentences = re.split(r"(?<=\.)\s", raw)
    for sentence in sentences:
        plain = text_of(sentence)
        if "eturn" not in plain:
            continue
        if re.search(r"is returned, otherwise <em>True</em> is returned", sentence) or ("otherwise True is returned" in plain):
            links = re.findall(r'<a href="#[a-z0-9_]+">([A-Z][A-Za-z]+)</a>', sentence)
            for link in links:
                if link in known:
                    return "?" + link
        array = re.search(r'(?:Array|array) of <a href="#[a-z0-9_]+">([A-Z][A-Za-z]+)</a>', sentence)
        if array and array.group(1) in known:
            return array.group(1) + "[]"
        if re.search(r"array of <a href=\"#message\">Messages?</a>", sentence, re.I) or "array of Messages" in plain:
            return "Message[]"
        if "array of MessageId" in plain or re.search(r"array of <a href=\"#messageid\">", sentence, re.I):
            return "MessageId[]"
        links = re.findall(r'<a href="#[a-z0-9_]+">([A-Z][A-Za-z]+)</a>', sentence)
        for link in links:
            if link in known:
                return link if link not in abstract else link
        if "<em>True</em>" in sentence or "True is returned" in plain or "Returns True" in plain:
            return "bool"
        if re.search(r"<em>Int</em>|Returns Int|as Int|Integer", sentence):
            return "int"
        if re.search(r"<em>String</em>|as String|String on success", sentence):
            return "string"
    return "bool"


def write_methods(methods, types, abstract, folder):
    known = {t["name"] for t in types} | HAND_WRITTEN
    out = ["// Generated by tools/generate.py from the Bot API reference; do not edit.\n",
           "partial module adm.notify.telegram {\n",
           "\tpartial type Bot {\n"]
    first = True
    for method in methods:
        name = method["name"]
        if name in HAND_WRITTEN_METHODS:
            continue
        rows = method["rows"]
        required, optional = [], []
        for row in rows:
            field = text_of(row[0])
            api = text_of(row[1])
            needed = text_of(row[2]) == "Yes"
            adm = adm_type(api, known, abstract, for_param=True)
            if field == "parse_mode":
                adm = "ParseMode"
            entry = (field, camel(field), adm)
            (required if needed else optional).append(entry)
        result = return_type(method, known, abstract)
        params = [f"{local} {adm}" for (_, local, adm) in required]
        for (_, local, adm) in optional:
            if adm.endswith("[]"):
                params.append(f"{local} {adm} = []")
            elif adm == "any":
                params.append(f"{local} ?any = none")
            else:
                params.append(f"{local} ?{adm} = none")
        if not first:
            out.append("\n")
        first = False
        out.append(comment(method["description"] or name, "\t\t"))
        out.append("\t\t// Fails as every call does.\n")
        out.append(f"\t\tdef {method_name(name)}({', '.join(params)}) !{result} {{\n")
        out.append("\t\t\tlet params = new map<string, any>()\n")
        for (field, local, adm) in required:
            out.append(f'\t\t\tparams.set("{field}", {local})\n')
        for (field, local, adm) in optional:
            if adm.endswith("[]"):
                out.append(f'\t\t\tparams.set("{field}", {local}) when {local}.len() > 0\n')
            elif adm == "ParseMode":
                out.append(f'\t\t\tparams.set("{field}", {local}.value) unless {local} is none\n')
            else:
                out.append(f'\t\t\tparams.set("{field}", {local}) unless {local} is none\n')
        base = result[1:] if result.startswith("?") else result
        if result == "bool":
            # The API answers `true` on success and fails otherwise.
            out.append(f'\t\t\ttry call(self, "{name}", params, none)\n')
            out.append("\t\t\treturn true\n")
            out.append("\t\t}\n")
            continue
        if base.endswith("[]"):
            out.append(f"\t\t\tlet reply = new Reply<{base}>()\n")
        elif base in ("int", "float", "string", "bool"):
            out.append(f"\t\t\tlet reply = new Reply<{base}>()\n")
        else:
            out.append(f"\t\t\tlet reply = new Reply<{base}>()\n")
            out.append(f"\t\t\treply.result = {base}{{}}\n")
        if result.startswith("?"):
            out.append(f'\t\t\treturn none unless try call(self, "{name}", params, reply)\n')
        else:
            out.append(f'\t\t\ttry call(self, "{name}", params, reply)\n')
        out.append("\t\t\treturn reply.result\n")
        out.append("\t\t}\n")
    out.append("\t}\n}\n")
    open(f"{folder}/methods.adm", "w").write("".join(out))
    write_method_tests(methods, known, abstract, folder)


def sample(adm):
    """A value of a parameter type, for a call that only has to reach the
    server."""
    if adm.endswith("[]"):
        return "[]"
    return {"int": "1", "float": "1.0", "string": '"x"', "bool": "true", "any": "42",
            "InputFile": 'fileId("x")'}.get(adm, adm + "{}")


def write_method_tests(methods, known, abstract, folder):
    out = ["// Generated by tools/generate.py from the Bot API reference; do not edit.\n",
           "partial module adm.notify.telegram {\n",
           "\tuse std.testing\n\n",
           '\tcheck "Telegram Bot API methods" {\n',
           "\t\t// Every method goes to its own name with its required parameters\n",
           "\t\t// under the API's names.\n",
           "\t\t@test()\n",
           "\t\tdef TestEveryMethodReachesItsName() !none {\n",
           "\t\t\tlet seen = new Seen()\n",
           "\t\t\tlet server = try telegramServer(seen)\n",
           "\t\t\tlet bot = botOf(seen)\n"]
    for method in methods:
        name = method["name"]
        if name in HAND_WRITTEN_METHODS:
            continue
        args, keys = [], []
        for row in method["rows"]:
            if text_of(row[2]) != "Yes":
                continue
            field = text_of(row[0])
            args.append(sample(adm_type(text_of(row[1]), known, abstract, for_param=True)))
            keys.append(f'"{field}"')
        out.append(f"\t\t\ttry bot.{method_name(name)}({', '.join(args)})\n")
        out.append(f'\t\t\ttry calledWith(seen, "{name}", [{", ".join(keys)}])\n')
    out.append("\t\t\ttry server.close()\n\t\t\treturn none\n\t\t}\n\t}\n}\n")
    open(f"{folder}/methods_test.adm", "w").write("".join(out))


def main():
    source, folder = sys.argv[1], sys.argv[2]
    document = open(source, encoding="utf-8").read()
    types, methods, abstract = parse(document)
    write_types(types, abstract, folder)
    write_methods(methods, types, abstract, folder)
    version = re.search(r"Bot API (\d+\.\d+)", document)
    print(f"Bot API {version.group(1) if version else '?'}: {len(types)} types, {len(methods)} methods")


if __name__ == "__main__":
    main()
