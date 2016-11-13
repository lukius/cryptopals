from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.tools.misc import Concatenation
        

class Set3Challenge19(CryptoChallenge):

    ANSWER_FILE = 'set3/data/19.txt'
    KEY = '\x8f\xc3\x7e\xfb\xc2\x00\x8f\x67\x22\xbe\xfd\xbe\xed\x6a\x39\xf7' +\
          '\x88\xc5\xf7\x8a\x0b\x83\x31\x38\xdc\x09\xc9\x0a\x2d\x1d\x55\x60' +\
          '\x9d\x7e\x7b\x7b\xea\xd1'
    
    def expected_value(self):
        decoded_lines = Base64Decoder().decode_file_lines(self.ANSWER_FILE)
        return Concatenation(decoded_lines).value()

    def value(self):
        # The ciphertexts were decrypted XORing consecutively one of them with
        # the others, trying to spot spaces. A space character xored with any 
        # letter will lowercase/uppercase it if it is an uppercase/lowercase
        # letter respecitvely:
        # >>> chr(ord(' ') ^ ord('X'))
        # 'x'
        # >>> chr(ord(' ') ^ ord('w'))
        # 'W'
        # This approach revealed several key bytes, and the remaning ones were
        # guessed completing partial words. The final key is shown above.
        # File set3/data/19enc.txt contains the base64-encoded ciphertexts,
        # which can be decrypted using this key.
        return '''I have met them at close of day
Coming with vivid faces
From counter or desk among grey
Eighteenth-century houses.
I have passed with a nod of the head
Or polite meaningless words,
Or have lingered awhile and said
Polite meaningless words,
And thought before I had done
Of a mocking tale or a gibe
To please a companion
Around the fire at the club,
Being certain that they and I
But lived where motley is worn:
All changed, changed utterly:
A terrible beauty is born.
That woman's days were spent
In ignorant good will,
Her nights in argument
Until her voice grew shrill.
What voice more sweet than hers
When young and beautiful,
She rode to harriers?
This man had kept a school
And rode our winged horse.
This other his helper and friend
Was coming into his force;
He might have won fame in the end,
So sensitive his nature seemed,
So daring and sweet his thought.
This other man I had dreamed
A drunken, vain-glorious lout.
He had done most bitter wrong
To some who are near my heart,
Yet I number him in the song;
He, too, has resigned his part
In the casual comedy;
He, too, has been changed in his turn,
Transformed utterly:
A terrible beauty is born.'''.replace('\n', '')       
        