# dependencies
from dbconfig import dbconfig
import mysql.connector
import re

# connect to maria db
try:
    connr = mysql.connector.connect(**dbconfig)
    dbr = connr.cursor(dictionary=True)
    connw = mysql.connector.connect(**dbconfig)
    dbw = connw.cursor()
except mysql.connector.Error as e:
    print(e)

# pre truncate for testing
#dbw.execute('TRUNCATE TABLE sentences')
#dbw.execute('TRUNCATE TABLE sentences_jobads')
#connw.commit()

# get harvested ads
dbr.execute('SELECT * FROM jobads WHERE crawled IS NOT NULL AND content != ""')

# predefine bullets
bullets = ['•', '·', '◾']

# get sentences from ads
for jobad in dbr:

    # progress
    try: num += 1
    except: num = 1
    if not num % 1000:
        print('{}K'.format(int(num / 1000)), flush=True)

    # split to lines
    lines = jobad['content'].split('\n')

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
    
    # add to db
    for i, sentence in enumerate(sentences):
        dbw.execute('INSERT INTO sentences (content) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)', [sentence])
        dbw.execute('INSERT IGNORE INTO sentences_jobads VALUES (LAST_INSERT_ID(), %s, %s)', [jobad['id'], i])
    connw.commit()

# kill db connection
dbr.close()
connr.close()
dbw.close()
connw.close()
