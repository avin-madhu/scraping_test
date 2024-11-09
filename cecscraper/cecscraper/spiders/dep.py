import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class CeconlineSpider(CrawlSpider):
    name = 'ceconline'
    allowed_domains = ['ceconline.edu']
    start_urls = ['https://ceconline.edu/']

    # Define rules to follow links within the specified path only
    rules = (
        Rule(LinkExtractor(allow=r'/.*'), callback='parse_page', follow=True),
    )

    def parse_page(self, response):
        # Extract the title of the page
        title = response.xpath(
            'normalize-space(//div[contains(@class, "title")]/text() | //h2[contains(@class, "custom_heading")]/text())'
        ).get()
        cleaned_title = self.clean_text(title)

        # Extract paragraphs (<p> tags) from the page
        paragraphs = response.xpath('//p/text()').getall()
        cleaned_paragraphs = [self.clean_text(p) for p in paragraphs]

        # Extract contact details (address, phone, email)
        contact_details = {
            'address': response.xpath('//li[contains(@class, "contact-details")]/text()').get(),
        }

        # Extract faculty details if present
        faculty,hod = self.parse_faculty_table(response)

        # Yield structured data as JSON
        if hod and faculty:
            yield {
            'url': response.url,
            'title': cleaned_title,
            'about': cleaned_paragraphs,
            'contact_details': contact_details,
            'faculty': faculty,
            'HOD': hod
        }
        else:
            if faculty:
                yield {
            'url': response.url,
            'title': cleaned_title,
            'about': cleaned_paragraphs,
            'contact_details': contact_details,
            'faculty': faculty,
            }
            else:
                yield {
            'url': response.url,
            'title': cleaned_title,
            'about': cleaned_paragraphs,
            'contact_details': contact_details,
            }

    def parse_faculty_table(self, response):
        # Locate the faculty table based on the headers
        faculty_data = []
        faculty_table = response.xpath('//h3[span[contains(text(), "Faculty")]]/following-sibling::table')

        # scrape the hod data
        hod_section = response.xpath('//div[contains(@class, "stm-teacher-bio__content")]')
        if hod_section:
            hod_name = hod_section.xpath('.//strong[contains(text(), "Dr.") or contains(text(), "Sri.") or contains(text(), "Smt.")]/text()').get()
            hod_title = hod_section.xpath('.//span[contains(@style, "font-size: 12pt")]/text()').get()
            department_address = hod_section.xpath('.//p/text()').getall()
            department_address = [self.clean_text(line) for line in department_address if line.strip()]

            hod = {
                'name': hod_name,
                'title': hod_title,
                'address': ' '.join(department_address)
            }
        else:
            hod = None
        

        # Skip the header row and parse each faculty row
        rows = faculty_table.xpath('.//tr[position()>1]')
        for row in rows:
            name = row.xpath('td[2]//text()').get()
            designation = row.xpath('td[3]//text()').get()
            faculty_data.append({
                "name": self.clean_text(name),
                "designation": self.clean_text(designation)
            })

        return faculty_data,hod

    def clean_text(self, text):
        """Clean text by removing unnecessary spaces and non-ASCII characters."""
        cleaned_text = text.strip() if text else ''
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove excessive spaces
        cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_text)  # Remove non-ASCII characters
        return cleaned_text
