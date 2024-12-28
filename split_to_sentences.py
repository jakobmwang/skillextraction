# define function to split text body
def split_to_sentences(body):

    # split to lines
    lines = body.split('\n')

    # define bullets
    bullets = ['•', '·', '◾']

    # split lines if not bullets
    splitted = []
    for line in lines:
        if line[0] in bullets and (split := line.strip()):
            splitted.append(split)
        else:
            abbrvs = ['\w.',
                      'ang.',
                      'dvs.',
                      'eks.',
                      'feks.',
                      'fx.',
                      '\w{1}nr.',
                      '\w{2}nr.',
                      '\w{3}nr.',
                      '\w{4}nr.',
                      '\w{5}nr.',
                      '\w{6}nr.',
                      '\w{7}nr.',
                      '\w{8}nr.',
                      'ca.',
                      'e.g.',
                      'i.e.',
                      'eg.',
                      'ie.',
                      'pr.',
                      'pt.',
                      'incl.',
                      'inkl.',
                      'max.',
                      'min.',
                      'ekskl.',
                      'mel.',
                      'osv.',
                      'mio.',
                      'mia.',
                      'mv.',
                      'etc.',
                      'kr.',
                      'kl.',
                      'bl.a.',
                      'bla.',
                      'b.la.',
                      'evt.',
                      'tlf.',
                      'ift.',
                      'lign.',
                      'approx.',
                      'pga.',
                      'vedr.']
            r = r'(?<!\b' + r')(?<!\b'.join([a.replace('.', r'\.') for a in abbrvs]) + r')(?<=[^\W0-9][\.\!\?](?=\s)(?![a-z]))'
            split = re.split(r, line, flags=re.IGNORECASE)
            splitted += [s for sp in split if (s := sp.strip())]

    # build sentences
    sentences = []
    for i, split in enumerate(splitted):

        # if prefix for bullet, continue
        if split[0] not in bullets and i + 1 < len(splitted) and splitted[i + 1][0] in bullets:
            sentences.append('')
            continue

        # append prefix if bullet
        if split[0] in bullets:
            for s in reversed(splitted[:i]):
                if s[0] not in bullets:
                    split = '{}{} {}'.format(s, ':' if s[-1] not in ['.', '!', '?', ':'] else '', (split + ' ')[1:].strip())
                    break

        # remove soft hyphens, control characters, zero width spaces, non-breaking spaces, and others
        split = re.sub(r'[\xad\x00-\x1f\x7f-\x9f\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u2060\xa0\ufeff]', '', split)

        # shorten if necessary
        split = re.sub(r'^(.{,251})\b.*$', r'\1', split, flags=re.I | re.M).strip() + ' ...' if len(split) > 255 else split

        # append
        sentences.append(split)

    return sentences
