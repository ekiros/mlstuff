##############################################################################################
#  The main command center that can be part of an automation, integation, or standalone script
#
# Data curation (including cleanup, normalizaion, etc.)
#   Files, Emails, Webpages, Chat, AV, etc
#       -> Store metadata 
#       -> Make data ready for indexing
#   Index data
# Analyze data: (optionally) store analytics against metadata
#       -> NLP 
# Enable Searching
#       -> Index + LLM
# Enable other functionalities
#       -> Word cloud
#       -> Categorization (k-means, Gaussian Mixture Models/EM)
#       -> Similarity scores for all files (TF-IDF)
#       -> Knowledge Extraction (LLM+)
#       -> Graphical presentation of relations
#       -> Q&A (e.g where was this image taken?)
#       -> AGI
#       -> Intentions
#

import os, sys

from PIL.Image import open
from PIL import ImageTk
from datetime import datetime
from tkinter import ttk
from tkinter import font

# To override the basic Tk widgets, the import should follow the Tk import
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

import textwrap

sys.path.insert(0, os.path.abspath(".."))

import search as S
import analytics.text_analytics.nl_analytics as NLP
from analytics.text_analytics import analytics_utils as Analytics_utils

"""
ttk example: editable input Text and readonly output Text with scrollbars.

Features:
 - Input (editable) on the left/top - enter your query here
 - Output (readonly) on the right/bottom - this is where the answer shows up - may be have a way rank answer
 - Buttons: Ask -> Trigger ML/AI for answer
 - Ctrl+Return sends input to output
 - Uses ttk styling and PanedWindow for resizable panes
"""
class Intellisearch(ttk.Frame):

    def __init__(self, parent):

        SEARCH_TITLE = "Intellisearch - Your Data. Your Search. Your Call."
        QUERY_PANE = "Your Questions Here"
        ANSWER_PANE = "Responses"
        HISTORY_PANE = "History"
     

        super().__init__(parent, padding=8)

        self.min_photo = self.close_photo = None
        self.max_length = 75

        self.parent = parent
        self.parent.title(SEARCH_TITLE)
        self.pack(fill="both", expand=True)

         # Styling
        style = Style()
        # Use the default theme but tweak font sizes if desired
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10)
        monospace = ("Courier New", 10)

        # Configure the default TButton style
        style.configure('TButton', font=('Arial', 12), foreground='blue')

        try:
            min_img = open("/Users/ekiros/docs/business/Microproduct_INC/marketing/microproduct-icon-only.ico")
        
            #Resize and convert to PhotoImage
            min_img = min_img.resize((48,48))
           
            self.min_photo = ImageTk.PhotoImage(min_img)

            self.parent.iconphoto(True, self.min_photo)

        except FileNotFoundError as fnf:
            print(f"Icon file not found: {fnf}")

        # Create a PanedWindow so user can resize panels
        paned = Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left frame (Input)
        left = Frame(paned, padding=(6,6))
        paned.add(left, weight=1)

        ttk.Label(left, text=QUERY_PANE).pack(anchor="w")
        input_frame = Frame(left)
        input_frame.pack(fill="both", expand=True)

        # Input Text + scrollbar
        self.input_text = Text(input_frame, wrap="word", font=(monospace, 12), undo=True)
        input_scroll = Scrollbar(input_frame, orient="vertical", command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scroll.set)
        self.input_text.pack(side="left", fill="both", expand=True)
        input_scroll.pack(side="right", fill="y")

        # Create middle panel to capture history
        center = Frame(paned, padding=(6,6))
        paned.add(center, weight=1)

        ttk.Label(center, text=HISTORY_PANE).pack(anchor="w")
        history_frame = Frame(center, width=250)
        history_frame.pack(fill="both", expand=True)
        history_frame.propagate(False)

        self.history_text = Text(history_frame, wrap="word", font=(monospace, 12), state="disabled")
        history_scroll = Scrollbar(history_frame, orient="vertical", command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_scroll.set)
        self.history_text.pack(side="left", fill="both", expand=True)
        history_scroll.pack(side="right", fill="y")

        # Right frame (Output)
        right = Frame(paned, padding=(6,6))
        paned.add(right, weight=1)

        ttk.Label(right, text=ANSWER_PANE).pack(anchor="w")
        output_frame = Frame(right)
        output_frame.pack(fill="both", expand=True)

        # Output Text + scrollbar (readonly)
        self.output_text = Text(output_frame, wrap="word", state="disabled")
        output_scroll = Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scroll.set)
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scroll.pack(side="right", fill="y")

        # Buttons below
        buttons = Frame(self, padding=(0,6,0,0))
        buttons.pack(fill="x")

        ask_btn = Button(buttons, text="Ask →", command=self.prompted_ask)
        analyze_sentiment_btn = Button(buttons, text="Analyze Sentiment", command=self.analyze_sentiment)
        summerize_btn = Button(buttons, text="Summerize", command=self.summerize_document)
        archive_hist_btn = Button(buttons, text="Archive History", command=self.archive_current)
        complete_btn = Button(buttons, text="No RAG Search", command=self.no_rag_search)
        clear_out_btn = Button(buttons, text="Clear Output", command=self.clear_output)

        ask_btn.pack(side='left', padx=(0,6))
        analyze_sentiment_btn.pack(side='left', padx=(0,6))
        complete_btn.pack(side='left', padx=(0, 8))
        summerize_btn.pack(side='left')

        archive_hist_btn.pack(side='right', padx=(0,8))
        clear_out_btn.pack(side='right', padx=(0, 8))

        # Bind the left mouse button click event (<Button-1>) to the on_click function
        #self.input_text.bind("<ButtonRelease>", lambda e: self.on_click())
        self.input_text.bind("<Return>", lambda e: self.on_enter()) #NOTE: We may have to have another handler for Windows
        #self.output_text.bind("<Key>", lambda e: self.ctrlEvent(e))

        # Keyboard shortcuts
        self.parent.bind("<Control-c>", lambda e: self.handle_ctrl_c())
        self.parent.bind("<Command-c>", lambda e: self.handle_ctrl_c())
        self.parent.bind_all("<Control-Return>", lambda e: self.prompted_ask())
        self.parent.bind_all("<Control-Delete>", lambda e: self.clear_input())

        # Optional: put some sample text in the input for demonstration
        #self.guide_input = "Type here and press Ask → or press Ctrl+Return..."
        #self.input_text.insert("1.0", self.guide_input)

    def on_click(self):
        self.clear_input()

    def on_enter(self):
        self.prompted_ask()
        self.clear_input()
    
    #NOTE: https://github.com/python/cpython/issues/104613 (bug where you cannot paste to BBEdit)
    def handle_ctrl_c(self):
        #print("ctrl-c called...")
        try:
            selected_txt = self.output_text.selection_get()
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected_txt)
            self.parent.update()

            #print(f"Copied text to clipboard: {selected_txt}")
            return "break"
        
        except TclError as te:
            print(f"something went wrong: {te}")

    # NOTE: We use RAG + LLM
    def prompted_ask(self):
        """Read input text and append it into the readonly output with a timestamp"""
        bg_prompt="#e1f7f7" 
        fg_prompt="red"   

        tag_name_in = "the_input_prompt"
        tag_name_out = "the_prompt_response"

        qry_font = font.Font(family='Courier', name='QRY_FONT_PROMPT', size=12, slant="italic")
        resp_font = font.Font(family='Calibri', name='RESP_FONT_PROMPT', size=14, weight="normal")

        self.output_text.tag_configure(tagName=tag_name_in, foreground=fg_prompt, background=bg_prompt, font=qry_font, justify='left')
        self.output_text.tag_configure(tagName=tag_name_out, font=resp_font)

        raw = self.input_text.get("1.0", "end-1c")
        #raw = self.input_text.get("end - 1c linestart", "end - 1c")
        if not raw.strip():
            return  # do nothing on empty input
        
        # Prepare message
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #your_question = "[Your Question was]: "
        #query = f"[{ts}] {your_question} {raw}\n"
        query = f"[{ts}] {raw.strip()}\n"

        #SEARCH_LOCATIONS =  ('chromadb','files')
        answer = S.search_i(query=raw, index_location=Analytics_utils.indexing_locations()[0])

        if answer is not None:
            answer += "\n\n"

        # Insert into output (must toggle state)
        self.output_text.configure(state="normal")
        self.output_text.insert("end", query,tag_name_in)
        self.output_text.insert("end", answer,tag_name_out)
        # optionally auto-scroll to the end
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

        # insert into the history
        self.__write_to_history(query, tag_name='prompt_tag', bg_color=bg_prompt, fg_color=fg_prompt)

        # Optionally clear input after sending
        self.clear_input()

    def no_rag_search(self):
        """Read input text and append it into the readonly output with a timestamp"""
        bg_norag_prompt="#e1f7f7" 
        fg_norag_prompt="red"   

        tag_name_in = "the_complete_input"
        tag_name_out = "the_complete_response"

        qry_font = font.Font(family='Courier', name='QRY_FONT_NORAG', size=12, slant="italic")
        resp_font = font.Font(family='Calibri', name='RESP_FONT_NORAG', size=14, weight="normal")

        self.output_text.tag_configure(tagName=tag_name_in, foreground=fg_norag_prompt, background=bg_norag_prompt, font=qry_font, justify='left')
        self.output_text.tag_configure(tagName=tag_name_out, font=resp_font)

        raw = self.input_text.get("1.0", "end-1c")
        #raw = self.input_text.get("end - 1c linestart", "end - 1c")
        if not raw.strip():
            return  # do nothing on empty input
        
        # Prepare message
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #your_question = "[Your Question was]: "
        #query = f"[{ts}] {your_question} {raw}\n"
        query = f"[{ts}] No RAG Search: {raw.strip()}\n"

        #SEARCH_LOCATIONS =  ('chromadb','files')
        answer = S.complete_chat_generic(raw)

        if answer is not None:
            answer += "\n\n"

        # Insert into output (must toggle state)
        self.output_text.configure(state="normal")
        self.output_text.insert("end", query,tag_name_in)
        self.output_text.insert("end", answer,tag_name_out)
        # optionally auto-scroll to the end
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

        # insert into the history
        self.__write_to_history(query, tag_name='tag_name_in', bg_color=bg_norag_prompt, fg_color=fg_norag_prompt)

        # Optionally clear input after sending
        self.clear_input()

    def analyze_sentiment(self):
        '''Given a sentence (or pragraph), analyze its sentiment/tone/polarity'''

        note = "  (sentiment scores range from -10 to 10. A score of -10 is highly negative and 10 is highly positive)\n\n"
        bg_sentiment = "#c1ffc1"

        qry_font = font.Font(family='Courier', name='QRY_FONT_SENT', size=12, slant="italic")
        resp_font = font.Font(family='Calibri', name='RESP_FONT_SENT', size=14, weight='normal')

        tag_name_in = "the_sentiment_text"
        tag_name_out = "the_sentiment_score"

        self.output_text.tag_configure(tagName=tag_name_in, background=bg_sentiment, font=qry_font, justify='left')
        self.output_text.tag_configure(tagName=tag_name_out, font=resp_font)
    
        paragraph = self.input_text.get("1.0", "end-1c")
        #paragraph = self.input_text.get("end - 1c linestart", "end - 1c")
        if not paragraph.strip():
            return  # do nothing on empty input

        intro = "[Sentiment Analyses]\n"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        input_data = f"[{ts}] {intro} {paragraph.strip()}\n"
        #score = f"The sentiment score for the above is: {NLP.normalized_sentiment(paragraph)}{note}"
        score = f"The sentiment score for the above is: {NLP.sentiment_analyses_distilbert(paragraph)}{note}"

        # Insert into output (must toggle state)
        self.output_text.configure(state="normal")
        self.output_text.insert("end", input_data,tag_name_in)
        self.output_text.insert("end", score,tag_name_out)
        # optionally auto-scroll to the end
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

        self.__write_to_history(input_data,tag_name='sent_tag', bg_color=bg_sentiment)

        # Optionally clear input after sending
        self.clear_input()
    
    def summerize_document(self):

        summerize_this = self.input_text.get("1.0", "end-1c")
        #raw = self.input_text.get("end - 1c linestart", "end - 1c")
        if not summerize_this.strip():
            return  # do nothing on empty input

        bg_summ = "#f6caca"
        qry_font = font.Font(family='Courier', name='QRY_FONT_SUMM', size=12, slant='italic')
        resp_font = font.Font(family='Calibri', name='RESP_FONT_SUMM', size=14, weight='normal')

        tag_name_in = "summerize_text"
        tag_name_out = "summerize_score"

        self.output_text.tag_configure(tagName=tag_name_in, background=bg_summ, font=qry_font, justify='left')
        self.output_text.tag_configure(tagName=tag_name_out, font=resp_font)

        # Prepare message
        intro = "[Summerization]\n"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        input_data = f"[{ts}] {intro}{summerize_this.strip()}\n"

        summarized = NLP.summerize_document(input_data)
        if summarized is None or summarized == '':
            summarized = 'Failure: Unable to Summerize\n\n'
        else:
            summarized += '\n\n'

        # NOTE: Summerize by file and by paragraph
        self.output_text.configure(state="normal")
        self.output_text.insert("end", input_data, tag_name_in)
        self.output_text.insert("end", summarized, tag_name_out)
        # optionally auto-scroll to the end
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

        self.__write_to_history(input_data, tag_name='summ_tag', bg_color=bg_summ)

        # Optionally clear input after sending
        self.clear_input()
    
    def archive_current(self):
        NotImplementedError("Not yet implemented")
    
    def __write_to_history(self, text, tag_name, bg_color= "#f0f0f0", fg_color="#000000"):

        self.history_text.tag_configure(tagName=tag_name, foreground=fg_color, background=bg_color, justify='left')
        self.history_text.configure(state="normal")
        self.history_text.insert("end", textwrap.shorten(text,width=self.max_length,placeholder='...'), tag_name)
        self.history_text.insert("end", '\n\n')
        self.history_text.see("end")
        #self.history_text.tag_remove("history_tag")
        self.history_text.configure(state="disabled")

    #### Cleaning stuff ####
    def clear_input(self):
        self.input_text.delete("1.0", "end")
    
    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")

def main():
    root = Tk()
    root.minsize(500, 500)
    #root.geometry("900x500")
    #root.overrideredirect(True) # Gets rid of the OS-supplied Close, etc
    app = Intellisearch(root)
    root.mainloop()


## RUN ##
if __name__ == '__main__':
    main()