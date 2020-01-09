from ocr import OCR


def test_answer():
    ocr = OCR()
    ocr.init()
    old_read_primes = []
    old_filtered = 0
    old_read_primes, old_filtered = ocr.read_screen(old_read_primes, old_filtered)
    assert len(old_read_primes) == 4


if __name__ == "__main__":
    test_answer()
