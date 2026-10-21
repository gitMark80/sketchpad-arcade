#!/usr/bin/env python3
"""Builds the kid-safe word list for Sketch with Friends: src/assets/sketch-with-friends/words.txt

Source: the Hunspell en_US dictionary (/usr/share/hunspell/en_US.dic + .aff, from SCOWL), expanded with its
own prefix/suffix rules. Kept: lowercase a-z words of 2-11 letters. Dropped: capitalised entries (names,
places, brands), anything with an apostrophe, and anything on the blocklist below (rude, sexual, slur and
drug words, with their endings). Written front-coded to keep the file small: each line is
<number of letters shared with the previous word><rest of the word>, e.g. "cat", "3s" = "cats".

Run:  python3 tools/sketch-with-friends-words.py
"""
import re
from pathlib import Path

DIC = Path("/usr/share/hunspell/en_US.dic")
AFF = Path("/usr/share/hunspell/en_US.aff")
OUT = Path(__file__).resolve().parent.parent / "src" / "assets" / "sketch-with-friends" / "words.txt"

# Words a family game should never accept. Each entry blocks the word itself and the word with any ending
# (so "fart" also blocks "farts", "farted", "farting"). STEM_ANY entries are blocked anywhere inside a word.
BLOCK = """
ass asses arse arses asshole bastard bitch bitchy bloody bollock bollocks boob boobs booby bugger bum butt butthole
crap crappy damn damned dammit darn dick dickhead dildo douche dyke fag faggot fart frigging hell hellish horny
jerkoff jizz knob knockers lesbo nigga negro paki pecker penis piss pissed poop porn porno prick pube pubic pussy
queer rape raped rapes raping rapist retard retarded scrotum semen sex sexy sexual sexually sexed sexes sexing
shag slut slutty smut sodomy sod spic spunk testicle tit tits titty turd twat vagina vulva wank wanker whore wop
homo hooker harlot hussy floozy strumpet trollop nude nudes nudity naked orgasm erotic erotica fetish kinky lewd
lust lustful lusty seduce seduction semen sperm stripper striptease bdsm condom condoms viagra orgy orgies breast
breasts nipple nipples genital genitals genitalia anal anus rectum enema incest pedophile pervert perverted molest
molester masturbate grope groped groping fondle fondling bra bras panties thong
cocaine coke heroin marijuana weed meth methamphetamine opium opiate narcotic narcotics crackhead stoned stoner
hashish ganja reefer lsd ecstasy junkie overdose bong bongs
nazi nazis kike chink gook coon darky darkie honky cracker redneck spook wetback beaner gringo jap japs savage
savages tranny slave slaves lynch lynching suicide suicidal murder murdered murderer murderous kill killer
killing killings
"""
STEM_ANY = ["fuck", "shit", "cunt", "nigg", "fagg", "whore", "slut", "porn", "dildo", "rapist", "pedo", "masturb", "orgasm", "penis", "vagin", "bitch", "sex", "cocain", "phall", "prostitut", "pimp", "brothel", "nympho", "coit", "erotic", "sodom", "pederas", "marijuan", "amphetamin", "genital", "testic", "clitor", "fellat", "cunnil", "semen", "scrot"]

def rules():
    sfx, pfx = {}, {}
    lines = AFF.read_text(encoding="utf-8").splitlines()
    for ln in lines:
        p = ln.split()
        if len(p) >= 4 and p[0] in ("SFX", "PFX") and len(p) >= 5 and p[2] != "Y" and p[2] != "N":
            kind, flag, strip, add, cond = p[0], p[1], p[2], p[3], p[4]
            strip = "" if strip == "0" else strip
            add = "" if add == "0" else add.split("/")[0]
            (sfx if kind == "SFX" else pfx).setdefault(flag, []).append((strip, add, cond))
    return sfx, pfx

def match(word, cond, suffix=True):
    if cond == ".":
        return True
    rx = (cond + "$") if suffix else ("^" + cond)
    return re.search(rx, word) is not None

def expand(stem, flags, sfx, pfx):
    out = {stem}
    sufs = []
    for f in flags:
        for strip, add, cond in sfx.get(f, []):
            if match(stem, cond) and (not strip or stem.endswith(strip)):
                sufs.append(stem[: len(stem) - len(strip)] + add)
    out.update(sufs)
    for f in flags:
        for strip, add, cond in pfx.get(f, []):
            if match(stem, cond, False):
                out.add(add + stem[len(strip):])
                for w in sufs:
                    out.add(add + w[len(strip):])
    return out

# Two-letter words we accept (the dictionary also lists abbreviations like "cm" and "ft", so these are hand-picked).
TWO = set("ah am an as at aw ax be by do eh em en ex go ha he hi ho hm id if in is it la lo ma me mi mo mu my no nu oh oi ok om on or ow ox oy pa pi qi re so ta ti to uh um up us we xi ya ye yo".split())
# Real words with no vowel (a, e, i, o, u or y); every other vowel-less entry is an abbreviation.
NOVOWEL = set("brr hmm shh psst nth tsk pfft".split())
# Abbreviations, roman numerals and slurs that look like words.
ABBR = set("""abl abr acc adj adv agr alg amt ans arr att aud aug avg avn bal cal cen cir cit civ cyl dat dec deg del dep der dir
doz dpi dup ecu enc eng enl ert esp est exc exp exr ext fac fec fol fut fwy gov gro hwy hyp ign inc ind inf ins int inv isl jor
kab kep lii liq loq lur lvi lxi mfg mus nav neg obj obs oct opp ord org rel req res rev rte sci sec sem seq ser sig sym syn
usu uts bkcy btry cryst dlvy fyrd hgwy phys pkwy synd syst ttys tyg typ typw wkly xci xii xiv xix xvi xxi iii vii xor qto qty yrs
jew jews jewed jewing gyp gyps gypped yid yids wog wogs goy goys goyim cum cums dago dagos""".split())
ALLOW = {"butter", "butters", "buttered", "buttering", "heroine", "heroines", "hello", "shell"}

def blocked(w, block):
    if w in ALLOW:
        return False
    if any(s in w for s in STEM_ANY):
        return True
    if w in block:
        return True
    for b in block:
        if w.startswith(b) and len(b) >= 3 and w[len(b):] in ("s", "es", "ed", "d", "ing", "er", "ers", "y", "ies", "ier", "iest", "ly", "ish"):
            return True
    return False

def main():
    sfx, pfx = rules()
    block = set(BLOCK.split())
    words = set()
    for ln in DIC.read_text(encoding="utf-8").splitlines()[1:]:
        stem, _, flags = ln.partition("/")
        if not stem or not stem[0].islower():
            continue
        for w in expand(stem, flags, sfx, pfx):
            if not re.fullmatch(r"[a-z]{2,11}", w) or blocked(w, block) or w in ABBR:
                continue
            if len(w) == 2 and w not in TWO:
                continue
            if not re.search(r"[aeiouy]", w) and w not in NOVOWEL:
                continue
            if re.fullmatch(r"m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})", w) and w not in {"mix", "dim", "mid", "lid", "mild", "civic", "vivid", "mimic", "dill", "ill", "mill", "mi", "civil", "vim", "dix", "mil"}:
                continue
            if True:
                words.add(w)
    words |= TWO
    words = sorted(words)
    lines, prev = [], ""
    for w in words:
        k = 0
        while k < min(len(w), len(prev), 9) and w[k] == prev[k]:
            k += 1
        lines.append(f"{k}{w[k:]}")
        prev = w
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"{len(words)} words, {OUT.stat().st_size // 1024} KB -> {OUT}")

if __name__ == "__main__":
    main()
