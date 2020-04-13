import scrapy
from csv import DictWriter

from urllib.request import urlopen

'''

 @author: Jacob Justice

 This program automatically scrapes the stackoverflow job listings.
 The listings are formatted as such:
     there is a listings page that contains 25 listings:
         each listing contains the data I want to scrape
     the listings page contains a link to the next page
 
 The scraper first goes across each listings page and gathers links
 to each individual listing. Once the links to all the listings have been collected
 then the scraper visits each link and parses it for the data.

 Attributes I scrape:
     Company name: Name of the company
     Job type: Whether the job is full-time or part-time
     Job Title: Name of the job that the listing is for
     *Company Size: an approximate range of the size of the company in people
     *Company Type: Public or private
     *Role: A title describing the job more specifically
     *Industry: what industry the job is a part of
     *Experience level: level of experience the job requires
     Location: Where the job is located
     Technologies: What technologies the future employee would need to know to do the job
     Likes: aggregate counter of how many users "Liked" the job listing
     Dislikes: aggregate counter of how many users "Disliked" the job listing
     Hearts: aggregate counter of how many users "Hearted" the job listing
     Description: raw text of the job description
 *not in every job listing; defaults to N/A

 You could use this data to visualize which programming skills are in demand
 in different parts of the world. You could also process the description
 to try and fill in the other fields that employers often leave blank.

 To exceed the minimum requirements I:
     scrape ~400 pages (more if you start at an earlier page)

     use xpath exclusively for all scraping and crawling
     
     goes across multiple pages of the website as
     opposed to gathering links from one static page
    
     program knows when to stop scraping by checking
     if there is no chevron_right
     
     attributes I search for:
         next page url
         all job listing urls on a page
         job listing data (14 attributes)
     
     filter the value of how many likes/dislikes/hearts
     to be stored as an int
     
     ensure there are no duplicate job listings stored

 I've set the program to start at page 720 for demonstration purposes. But to have
 it scrape every listing go to the first line of start_requests and uncomment it,
 then comment out the next line.

'''

class JobSpider(scrapy.Spider):
    name = "jobs"
    base_url = "https://stackoverflow.com"
    page_urls = []

    write_obj = open("stackoverflow_jobs.csv","a+")
    field_names = [
    'job title',
    'company_name',
    'company_size',
    'company_type',
    'role',
    'industry',
    'experience_level',
    'location',
    'job type',
    'technologies',
    'likes',
    'dislikes',
    'hearts',
    'url',
    'description'
    ]
    dict_write = DictWriter(write_obj, fieldnames=field_names)

    unique_job_listings = set()

    def start_requests(self):
        url = "https://stackoverflow.com/jobs"
        #url = "https://stackoverflow.com/jobs?sort=p&pg=715"
        yield scrapy.Request(url=url, callback=self.gather_pages)


    def gather_pages(self, response):
        next_button_link = response.xpath("//a[@class='s-pagination--item']/i[text()='chevron_right']//parent::a/@href").get()
        if next_button_link != None:
            page_url = self.base_url + next_button_link
        else:
            print("\n\n\n", "no more pages")
            page_url = None
        links = response.xpath("//h2[@class='mb4 fc-black-800 fs-body3']/a/@href").getall()
        self.unique_job_listings.update(links)

        print("number of listings",len(self.unique_job_listings))

        if page_url != None:
            self.page_urls.append(page_url)
            yield scrapy.Request(url=page_url, callback=self.gather_pages)
        else:
            for url in self.unique_job_listings:
                listing_url = self.base_url + url
                yield scrapy.Request(url=listing_url, callback=self.gather_listing_info)

    def gather_listing_info(self, response):
        listing_info_dict = self.stackoverflow_job_info(response.url, response)

        if listing_info_dict != None:
            self.dict_write.writerow(listing_info_dict)
            yield listing_info_dict

    def stackoverflow_job_info(self, url, response):
        output = {}

        #company name
        #
        company_text = response.xpath("//div[@class='fc-black-700 fs-body3']/text()").get().strip().replace('\r', '').replace('\n', '')
        if company_text == '':
            company_text = response.xpath("//div[@class='fc-black-700 fs-body3']/a/text()").get().strip().replace('\r', '').replace('\n', '')
        if company_text == '':
            company_text = "N/A"
        output.update({'company_name':company_text})

        #job type
        #company size
        #company type
        #role
        #industry
        #experience_level
        #
        mb8_text = response.xpath("//div[@id='overview-items']//div[@class='mb8']/span/text()").getall()

        job_type = 'N/A'
        company_size = 'N/A'
        company_type = 'N/A'
        role = 'N/A'
        industry = 'N/A'
        experience_level = 'N/A'
        for i, text in enumerate(mb8_text):
            if 'Job type: ' == text:
                job_type = mb8_text[i+1]
            elif 'Company size: ' == text:
                company_size = mb8_text[i+1]
            elif 'Company type: ' == text:
                company_type = mb8_text[i+1]
            elif 'Role: ' == text:
                role = mb8_text[i+1]
            elif 'Industry: ' == text:
                industry = mb8_text[i+1]
            elif 'Experience level: ' == text:
                experience_level = mb8_text[i+1]

        output.update( {'job type' : job_type.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'company_size' : company_size.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'company_type' : company_type.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'role' : role.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'industry' : industry.strip().replace('\r', '').replace('\n', '')} )
        output.update( {'experience_level' : experience_level.strip().replace('\r', '').replace('\n', '')} )


        #technologies
        #
        technologies = response.xpath("//section[@class='mb32']/div/a[@class='post-tag job-link no-tag-menu']/text()").getall()
        output.update({'technologies' : technologies})

        #job title
        #
        output.update({'job title':
            response.xpath("//a[@class='fc-black-900']/text()").get().replace('\r', '').replace('\n', '')})

        #location
        #
        location = (response.xpath("//span[@class='fc-black-500']/text()").get().strip())
        location = location[3:].replace('\r', '').replace('\n', '')
        output.update({'location':location})

        #likes
        #
        output.update({"likes":int(
            response.xpath("//span[@title='Like']/span/text()").get())})

        #dislikes
        #
        output.update({"dislikes":int(
            response.xpath("//span[@title='Dislike']/span/text()").get())})
        
        #hearts
        #
        output.update({"hearts":int(
            response.xpath("//span[@title='Love']/span/text()").get())})

        #url
        #
        output.update({"url":url})

        #description
        #
        section_text = ""
        description = response.xpath("//h2[text()='Job description']/..//text()").getall()

        del description[:2]

        for tag in description:
            section_text += tag.replace('\r', ' ').replace('\n', ' ').replace('\xa0', ' ')
        output.update({'description':section_text.strip()})

        return output
