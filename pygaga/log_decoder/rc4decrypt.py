# coding=utf-8

rc4_key = "\x13\x23\xae\x9e\x12\x52\xaf\x83\xf7\xe1\x21\x77\x21\x33\xcd\xe2"

def rc4decrypt(data, key=rc4_key):
    x = 0
    box = range(256)
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = 0
    y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

    return ''.join(out)

if __name__ == '__main__':
    data = 'hello world!'
    encryptdata = rc4decrypt(data, rc4_key)
    print "%s after encrypt: " % (data)
    print encryptdata
    decryptdata = rc4decrypt(encryptdata, rc4_key)
    print "after decrypt: "
    print decryptdata
