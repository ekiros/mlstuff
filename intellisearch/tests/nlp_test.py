import os, sys, logging


sys.path.insert(0, os.path.abspath(".."))
from analytics.text_analytics import nl_analytics as NLP

logger = logging.getLogger(__name__)

logger.setLevel("INFO")
logging.basicConfig(filename="intelli_nlp.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")

def main():
    test_nlp_sentiment()
    #test_nlp_summerization()

def test_nlp_sentiment():
    normalize_by=10

    sentences = [ 
        "Most automated sentiment analysis tools are shit.", 
        "VADER sentiment analysis is the shit.",
        "Sentiment analysis has never been good.",
        "Sentiment analysis with VADER has never been this good.", 
        "Warren Beatty has never been so entertaining.",
        "I won't say that the movie is astounding and I wouldn't claim that the movie is too banal either.",
        "I like to hate Michael Bay films, but I couldn't fault this one",
        "I like to hate Michael Bay films, BUT I couldn't help but fault this one",
        "It's one thing to watch an Uwe Boll film, but another thing entirely to pay for it",
        "The movie was too good" 
    ]

    p1 = "It was one of the worst movies I've seen, despite good reviews. \
    ... Unbelievably bad acting!! Poor direction. VERY poor production. \
    ... The movie was bad. Very bad movie. VERY bad movie. VERY BAD movie. VERY BAD movie!"

    p2 = "I've had Love You Latte bookmarked for a long time & I finally had a chance to go. Everything was exceptional! \
    ... We ordered the salmon toast, mozza bella, chorizo tostada, & strawberry matcha. Every single dish was delicious. \
    ... The pesto in the mozza bella was so good! My mom ordered the salmon toast & it's topped with pickled onions. \
    ... She hates onions, but really enjoyed eating these ones! The portions were perfect. We all had full tummies \
    ... & empty plates. The service was also exceptional. Kostas was very friendly & came around to our table many times \
    ... to check on us & make sure everything was good. He even brought extra sauce & waters without us asking for it, \
    ... & a coupon for our next visit! This was definitely an enjoyable place to have brunch/ lunch!"

    p3 = "The range is mud. The course is whatever. But if you want to play golf and don't want to \
    ... spend that much money to do so then this place will do in a pinch. Two stars. Anything above \
    ... that the rather is a liar"

    p4 = "Altadena Golf Course is a public golf course by city with hole 9 lengths 2,995 yards. \
    ... Fairways are mostly flat and wide enough for beginners. The number of carts is not enough; \
    ... therefore, there is a chance of waiting to get a golf cart. It is a cozy course to enjoy \
    ... simple 9 holes for fun."

    p5 = "Hi Eskinder,I’m sorry to hear of this. Happy to schedule a call to discuss next steps. \
        I’ve included Ian from the brand team for visibility and any assistance you made need from \
            the brand side. I’ve also included Katie of our equipment team for visibility, replacements \
                if any millwork and/or equipment for the studio.  Photos will be key for both our \
                    vendors & your insurance company.Here to assist in any way I can."

    a_file = '/Users/ekiros/Downloads/complete fasting-14-03860.pdf'
    
    logger.info("=================== Testing Sentiment Analyses ===================")
    #logger.info(f"[P1] Overall Sentiment score = {NLP.normalized_sentiment(p1,normalize_by)}")
    #logger.info(f"[P2] Overall Sentiment score = {NLP.normalized_sentiment(p2,normalize_by)}")
    #logger.info(f"[P3] Overall Sentiment score = {NLP.normalized_sentiment(p3,normalize_by)}")
    logger.info(f"[P4] Overall Sentiment score = {NLP.normalized_sentiment(p3,normalize_by)}")

    #logger.info(f"[Sentiment Anlyses on a File] Overall Sentiment score = {NLP.normalized_sentiment_file(a_file)}")

    logger.info(f"[Sentiment Anlyses using LLM] Overall Sentiment score = {NLP.sentiment_analyses_distilbert(p3)}")


def test_nlp_summerization():

    # Test Summary ##
    logger.info("=================== Testing Document Summarization ===================")

    doc_long = "Time will tell. SGEK Business Group LLC d/b/a Pure Barre (the \"Company\") was established with the intention of engaging in business \
    ... activities in the fitness industry. Specifically, the Company intends to open one or more studios as a franchisee of Pure \
    ... Barre Franchise, LLC (“Pure Barre”).  The Company is prepared to launch a Pure Barre studio in Sunnyvale, CA. Millennials \
    ... considered as the “wellness generation,” with 79% of Americans aged 26-40 stating health as the most important thing in \
    ... their lives, second only to family. For this reason, Millennials have caught the attention of boutique studios, wearable \
    ... developers, and equipment manufacturers. Considering the fitness industry growth outlined below in section [2.0], Pure Barre \
    ... is currently the largest brand and one of the fastest-growing franchises in the US, leading a rapid nationwide expansion of \
    ... the franchise with new locations opening across the US every month. Pure Barre is ranked in Entrepreneur Magazine’s Franchise \
    ... 500 eight years running and in the Fastest-Growing Franchises in 2021 as well as Inc, Magazine’s Inc. 5000 in 2020. Pure Barre \
    ... originated in Birmingham, MI and currently has approximately [640] studios open across the United States. Pure Barre aims to deliver \
    ... the finest strength-training workout available for anyone, at any age, and to create a community that brings the benefits of Pure Barre \
    ... to everybody for a path to a fuller, richer, healthier and more satisfying life.  The Pure Barre team has more combined hours studying, \
    ... training, teaching and practicing barre than any other barre studio in existence. Through such experience, Pure Barre has perfected its \
    ... unique and proprietary approach to ensuring every Pure Barre client receives the finest training and most effective results. Pure Barre \
    ... has an established business model for its studios. Key factors of the Pure Barre Method include but are not limited to: The widest array \
    ... of barre classes available anywhere, led by Certified Instructors, designed to challenge clients at every level Brand-new state of the \
    ... art equipment in every studio including Pure Barre dumbbells, Elastic bands, barre, and the training Choreography. The best value in barre, \
    ... that allows more consumers to dedicate themselves to Pure Barre for life Pure Barre studios offer the following services and products to consumers: \
    ... Equipment-based Pure Barre Classes – Group Sessions; Equipment-based Pure Barre Classes – Private Training Sessions; Retail & Merchandise \
    ... The Company will target active men and women between 18 and 75 with a median household income of $75,000+, who are interested in improving their \
    ... physique, energy, vigor and strength.  Competition will come from local independent barre studios, other similar boutique fitness studios (e.g., \
    ... barre, yoga, etc.) and to a lesser extent general fitness facilities in the area. The Pure Barre studios operating in similar areas have proven the \
    ... model to create a consistent membership base for their studios. Additionally, the Pure Barre brand is increasingly expanding its awareness and following. \
    ... This will further set the Company apart from other competitors in this area.To attract its intended target audience and membership base, the Company \
    ... will employ a variety of multimedia channels that will emphasize its superior workout programs and commitment to client satisfaction. The Company will \
    ... implement a marketing strategy including direct and online marketing tactics aimed to increase overall awareness of its facilities and the Pure Barre brand. \
    ... Advertising mediums will include social media, direct mail, radio and television ads, in-store marketing, e-mail blasts, billboards, and flyers. To launch the \
    ... first Pure Barre studio currently planned for the Sunnyvale, CA location, achieve its objectives, the Company solicits total funding of $500,000 as further \
    ... detailed in section [1.5]. Millennials are considered as the “wellness generation,” with 79% of Americans aged 26-40 stating health as the most important thing \
    ... in their lives, second only to family. For this reason, Millennials have caught the attention of boutique studios, wearable developers, and equipment manufacturers. \
    ... In the United States alone, the fitness industry has grown by more than $32B in 2018, reflecting an 8% increase over the prior year. Post the pandemic the health \
    ... & fitness industry is rebounding with a staggering revenue of $35.03B as of 2023. Considering the fitness industry growth outlined above, Pure Barre is currently the \
    ... largest brand and one of the fastest-growing franchises in the US, leading a rapid nationwide expansion of the franchise with new locations opening across the US every \
    ... month. Pure Barre is ranked in Entrepreneur Magazine’s Franchise 500 eight years running and in the Fastest-Growing Franchises in 2021 as well as Inc, Magazine’s Inc. \
    ... 5000 in 2020. Pure Barre originated in Birmingham, MI and currently has approximately [612] studios open across the United States. \
    ... Pure Barre aims to deliver the finest strength-training workout available for anyone, at any age, and to create a community that brings the benefits of Pure \
    ... Barre to everybody for a path to a fuller, richer, healthier and more satisfying life.  The Pure Barre team has more combined hours studying, training, teaching \
    ... and practicing barre than any other barre studio in existence. Through such experience, Pure Barre has perfected its unique and proprietary approach to ensuring \
    ... every Pure Barre client receives the finest training and most effective results. \
    ... The Company’s mission statement is as follows: “Deliver a consistently superior barre experience, at a price that enables Pure Barre members to commit to Pure Barre \
    ... for life.” Pure Barre has an established business model for its studios. Key factors of the Pure Barre Method include but are not limited to: \
    ... • The widest array of barre classes available anywhere, led by Certified Instructors, designed to challenge clients at every level \
    ... • Brand-new state of the art equipment in every studio including Pure Barre dumbbells, Elastic bands, barre, and the training Choreography \
    ... • The best value in barre, that allows more consumers to dedicate themselves to Pure Barre for life \
    ... Pure Barre studios offer the following services and products to consumers: \
    ... • Equipment-based Pure Barre Classes – Group Sessions \
    ... • Equipment-based Pure Barre Classes – Private Training Sessions \
    ... • Retail & Merchandise \
    ... The Company will target active men and women between 18 and 75 with a median household income of $75,000+, who are interested in improving their physique, energy, \
    ... vigor and strength.  Competition will come from local independent barre studios, other similar boutique fitness studios (e.g., barre, yoga, etc.) and to a lesser extent \
    ... general fitness facilities in the area. The Pure Barre studios operating in similar areas have proven the model to create a consistent membership base for their studios. \
    ... Additionally, the Pure Barre brand is increasingly expanding its awareness and following. This will further set the Company apart from other competitors in this area. \
    ... The primary target demographic for a Pure Barre studio is youthful and active men and women between 18 and 75 with a median household income of $75,000+, who are interested \
    ... in improving their physique, energy, vigor and strength. However, the customer base will likely be mostly health-conscious women who are passionate about barre and life. We \
    ... will be in the South Bay of the San Francisco Bay Area, California. The cities in our area of development (ADA) include Sunnyvale, Santa Clara, and the Willow Glenn neighborhood \
    ... of San Jose. The following is the demographic info for the Sunnyvale area (which is what we are planning to develop first): \
    ... Total Population: 152,876 \
    ... Total Households: 58,955 \
    ... Female Population: 75,058 \
    ... Daytime Population 145,098 \
    ... Median Age: 37.60 \
    ... AVG Household income: $194,286 \
    ... Total Core Customer Households: 22,223 \
    ... Hours of business operation will be 6:00am - 8:00pm, Monday through Sunday (or seven days a week)"
    
    doc_short = "Time will tell. SGEK Business Group LLC d/b/a Pure Barre (the \"Company\") was established with the intention of engaging in business \
    ... activities in the fitness industry. Specifically, the Company intends to open one or more studios as a franchisee of Pure \
    ... Barre Franchise, LLC (“Pure Barre”).  The Company is prepared to launch a Pure Barre studio in Sunnyvale, CA. Millennials \
    ... considered as the “wellness generation,” with 79% of Americans aged 26-40 stating health as the most important thing in \
    ... their lives, second only to family. For this reason, Millennials have caught the attention of boutique studios, wearable \
    ... developers, and equipment manufacturers. Considering the fitness industry growth outlined below in section [2.0], Pure Barre \
    ... is currently the largest brand and one of the fastest-growing franchises in the US, leading a rapid nationwide expansion of \
    ... the franchise with new locations opening across the US every month. Pure Barre is ranked in Entrepreneur Magazine’s Franchise \
    ... 500 eight years running and in the Fastest-Growing Franchises in 2021 as well as Inc, Magazine’s Inc. 5000 in 2020. Pure Barre \
    ... originated in Birmingham, MI and currently has approximately [640] studios open across the United States. Pure Barre aims to deliver \
    ... the finest strength-training workout available for anyone, at any age, and to create a community that brings the benefits of Pure Barre \
    ... to everybody for a path to a fuller, richer, healthier and more satisfying life.  The Pure Barre team has more combined hours studying, \
    ... training, teaching and practicing barre than any other barre studio in existence. Through such experience, Pure Barre has perfected its \
    ... unique and proprietary approach to ensuring every Pure Barre client receives the finest training and most effective results. Pure Barre \
    ... has an established business model for its studios. Key factors of the Pure Barre Method include but are not limited to: The widest array \
    ... of barre classes available anywhere, led by Certified Instructors, designed to challenge clients at every level Brand-new state of the \
    ... art equipment in every studio including Pure Barre dumbbells, Elastic bands, barre, and the training Choreography. The best value in barre, \
    ... that allows more consumers to dedicate themselves to Pure Barre for life Pure Barre studios offer the following services and products to consumers: \
    ... Equipment-based Pure Barre Classes – Group Sessions; Equipment-based Pure Barre Classes – Private Training Sessions; Retail & Merchandise \
    ... The Company will target active men and women between 18 and 75 with a median household income of $75,000+, who are interested in improving their \
    ... physique, energy, vigor and strength."
 
    logger.info(f"[Summary] {NLP.summerize_document(doc_short)}")
    #logger.info(f"[Summary_long] {NLP.summerize_document(doc_long)})")
    #logger.info(f"[Summary_nopipe] {NLP.summerize_doc_nopipe(doc_long)}")

    a_pdf_file = "/Users/ekiros/Downloads/NEW SEASON STEP-BY-STEP PDF.pdf"
    a_doc_file = '/Users/ekiros/Downloads/Lease Form - Tri-Party & Landlord Waiver.docx'
    a_csv_file = '/Users/ekiros/Downloads/transactions-13082024.csv'
    a_jpg_file = '/Users/ekiros/Downloads/marlin-clark-vi4DEQIpYAM-unsplash.jpg'
    an_xls_file = '/Users/ekiros/Downloads/scyslreg072924teamsu12gKIROS.xlsx'


    #logger.info(f"[Summarize a File] {NLP.summerize_file(a_pdf_file)}")

## RUN ##
if __name__ == '__main__':
    main()
