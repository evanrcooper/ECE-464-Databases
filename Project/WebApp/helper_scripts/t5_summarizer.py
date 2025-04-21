import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from nltk.tokenize import sent_tokenize
import sys

nltk.download('punkt_tab')

def is_gpu_sufficient(min_vram_gb=6):
    if not torch.cuda.is_available():
        return False
    try:
        props = torch.cuda.get_device_properties(0)
    except Exception as e:
        return False
    props = torch.cuda.get_device_properties(0)
    return props.total_memory >= min_vram_gb * 1_000_000_000

class T5Summarizer:
    def __init__(self, model_name: str = 'T5-base', sentence_count = None):
        # [T5 for Text Summarization in 7 Lines of Code](https://medium.com/artificialis/t5-for-text-summarization-in-7-lines-of-code-b665c9e40771)
        # [Google's T5](https://github.com/google-research/text-to-text-transfer-transformer#released-model-checkpoints)
        model_names = ['T5-small', 'T5-base', 'T5-large', 'T5-3B', 'T5-11B']
        assert model_name in model_names, f'model_name must be one of: {model_names}.'
        self.model_name = model_name
        # self.device = 'cuda' if is_gpu_sufficient(min_vram_gb=4) else 'cpu'
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, return_dict=True)
        self.model.to(self.device)

    # def generate_summary(self, text: str, min_length: int = 80, max_length: int = 600) -> str:
    #     try:
    #         inputs = self.tokenizer.encode("summarize: " + text, return_tensors='pt', max_length=1024, truncation=True).to(self.device)
    #         output = self.model.generate(inputs, min_length=min_length, max_length=max_length)
    #         decoded_output = self.tokenizer.decode(output[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    #         sentences = sent_tokenize(decoded_output)
    #         fixed_sentences = [s.capitalize() for s in sentences]
    #         summary = ' '.join(fixed_sentences)
            
    #     except Exception as e:
    #         sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
    #         sys.stderr.write(f'Unable to generate summary.')
    #         summary = None
    #     if summary is None or len(summary) <= 1:
    #         return False, 'No summary available.'
    #     return True, summary

    def dedup_sentences(self, text):
        seen = set()
        result = []
        for sentence in sent_tokenize(text):
            s = sentence.strip()
            if s and s not in seen:
                seen.add(s)
                result.append(s)
        return ' '.join(result)

    def generate_summary(self, text: str, min_length: int = 64, max_length: int = 512) -> tuple[bool, str]:
        try:
            prompt = 'summarize: ' + text
            inputs = self.tokenizer.encode(prompt, return_tensors='pt', max_length=4096, truncation=True).to(self.device)
            output = self.model.generate(
                inputs,
                min_length=min_length,
                max_length=max_length,
                no_repeat_ngram_size=3,
                num_beams=4,
            )
            decoded_output = self.tokenizer.decode(output[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
            cleaned = self.dedup_sentences(decoded_output)
            sentences = sent_tokenize(cleaned)
            fixed_sentences = [s[0].upper() + s[1:] if s else "" for s in sentences]
            summary = ' '.join(fixed_sentences)
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write('Unable to generate summary.\n')
            return False, 'No summary available.'
        if not summary or len(summary) < 10:
            return False, 'No summary available.'
        return True, summary
