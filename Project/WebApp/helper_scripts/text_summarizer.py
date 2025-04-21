import sys
import spacy
import pytextrank
import spacy.cli

class TextRanker:
    def __init__(self, sentence_count: int = 5, model_name = None) -> None:
        self.sentence_count: int = sentence_count
        spacy.cli.download("en_core_web_sm")
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe("textrank")

    def generate_summary(self, text: str) -> tuple[bool, str]:
        doc: str = self.nlp(text)
        try:
            summary: str = ' '.join([sent.text.strip() for sent in doc._.textrank.summary(limit_sentences=self.sentence_count)])
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            return (False, 'Unable to generate summary.')
        if len(summary) > 0 and len(summary) < 2048:
            return (True, summary)
        return (False, 'Unable to generate summary.')