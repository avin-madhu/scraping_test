import scrapy
import re

class CeconlineSpider(scrapy.Spider):
    name = 'ceconline'
    allowed_domains = ['ceconline.edu']
    start_urls = ['https://ceconline.edu']
    departments = ['https://ceconline.edu/academics/departments']

    def parse(self, response):
        # Extract the menu links with their text (e.g., "KTU", "Programs", etc.)
        menu_links = response.xpath('//li[contains(@class, "menu-item")]/a/@href').getall()
        print(menu_links, "\n\n\n\n\n\n\n\n\n\n")
        # Loop through each link in the menu
        for link in menu_links:
            yield response.follow(link, self.parse_page)

    def parse_page(self, response):
        # Extract the title of the page
        title = response.xpath('//div[contains(@class, "title")]/text() | //h2[contains(@class, "custom_heading")]/text()').get()
        cleaned_title = self.clean_text(title)

        # Extract paragraphs (<p> tags) from the page
        paragraphs = response.xpath('//p/text()').getall()
        cleaned_paragraphs = [self.clean_text(p) for p in paragraphs]

        # Extract contact details (address, phone, email)
        contact_details = {
            'address': response.xpath('//li[contains(@class, "contact-details")]/text()').get(),
        }
        
        faculty = self.parse_faculty_table(response)

        # Yield structured data as JSON
        yield {
            'url': response.url,
            'title': cleaned_title,
            'about': cleaned_paragraphs,
            'contact_details': contact_details,
            'faculty': faculty,
        }

    def parse_faculty_table(self, response):
        # Locate the faculty table based on the headers
        faculty_data = []
        faculty_table = response.xpath('//h3[span[contains(text(), "Faculty")]]/following-sibling::table')

        # Skip the header row and parse each faculty row
        rows = faculty_table.xpath('.//tr[position()>1]')
        for row in rows:
            sl_no = row.xpath('td[1]/text()').get()
            name = row.xpath('td[2]//text()').get()
            designation = row.xpath('td[3]//text()').get()
            faculty_data.append({
                "name": self.clean_text(name),
                "designation": self.clean_text(designation)
            })

        return faculty_data
            
        # Yield the data in a structured format

    def clean_text(self, text):
        """Clean text by removing unnecessary spaces and non-ASCII characters."""
        # Strip leading/trailing spaces
        cleaned_text = text.strip() if text else ''
        # Remove excessive spaces between words
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        # Remove any non-ASCII characters
        cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_text)
        return cleaned_text
