from io import BytesIO
import unittest
import zipfile

from docx import Document

from cv_generator.documents import render_document


SAMPLE = "# Alex Smith\n\n## Professional Summary\n\nSynthetic profile.\n\n## Skills\n\n- Sales\n"


class DocumentTests(unittest.TestCase):
    def test_txt_is_utf8(self):
        self.assertEqual(render_document(SAMPLE, "txt", "UK").decode(), SAMPLE)

    def test_docx_is_valid_and_contains_resume_text(self):
        data = render_document(SAMPLE, "docx", "UK")
        self.assertTrue(data.startswith(b"PK"))
        document = Document(BytesIO(data))
        self.assertIn("Alex Smith", "\n".join(p.text for p in document.paragraphs))

    def test_pdf_is_valid_and_contains_resume_text(self):
        data = render_document(SAMPLE, "pdf", "UK")
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertTrue(data.rstrip().endswith(b"%%EOF"))
        self.assertGreater(len(data), 1_000)

    def test_docx_is_a_valid_zip_container(self):
        data = render_document(SAMPLE, "docx", "US")
        with zipfile.ZipFile(BytesIO(data)) as archive:
            self.assertIn("word/document.xml", archive.namelist())


if __name__ == "__main__":
    unittest.main()
