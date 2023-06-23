import requests
from bs4 import BeautifulSoup
import json 
import concurrent.futures

base_url="https://www.flipkart.com";
q="all+iphone";
url = base_url+"/search?q="+str(q);
data=[];


def getText(element):
    if(element):
       return element.text.strip();
    else:
        return "";

def getTableData(element):
    data_dict = {};
    for row in element.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) > 0:
            key = cells[0].text.strip()
            if(key and len(cells) > 1):
                value = cells[1].text.strip()
                data_dict[key] = value
    return data_dict;

def getGridData(element):
    details = {}
    rows = element.find_all("div", class_="row")

    def getRowData(row):
        data = {}
        key_element = row.find(class_="col col-3-12 _2H87wv")
        value_element = row.find(class_="col col-9-12 _2vZqPX")
        key = getText(key_element)
        value = getText(value_element)
        if key:
            data[key] = value
            return data

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_rows = {executor.submit(getRowData, row): row for row in rows}
        for future in concurrent.futures.as_completed(future_rows):
            row = future_rows[future]
            try:
                data = future.result()
                if data:
                    print(data)
                    details.update(data)
            except Exception as e:
                print(f"Error processing tool: {str(e)}")

    details["description"] = getText(element.find("div", class_="_1AN87F"))
    return details

def getTooltip(li_tooltip, product):
    storage = []
    color = []
    ram = []
    size = []
    washing_capacity = []
    wifi_connectivity = [] 
    def process_tool(tool):
        id = tool["id"]
        text = tool.find("div", class_="_2OTVHf _3NVE7n _1mQK5h _2J-DXM")
        if text:
            return text.text
 
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor: 
        future_to_tool = {executor.submit(process_tool, tool): tool for tool in li_tooltip}
 
        for future in concurrent.futures.as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                result = future.result()
                if not result:
                    continue
                id = tool["id"]
                if "storage" in id:
                    storage.append(result)
                if "ram" in id:
                    ram.append(result)
                if "color" in id:
                    color.append(result)
                if "size" in id:
                    size.append(result)
                if "washing_capacity" in id:
                    washing_capacity.append(result)
                if "wifi_connectivity" in id:
                    wifi_connectivity.append(result)
            except Exception as e: 
                print(f"Error processing tool: {str(e)}")

    product["storage"] = storage
    product["color"] = color
    product["ram"] = ram
    product["size"] = size
    product["washing_capacity"] = washing_capacity
    product["wifi_connectivity"] = wifi_connectivity


def process_product(link):
      product={};
      product["product_link"]=base_url+link['href'];
      product_page=requests.get(base_url+link['href'])
      product_soup=BeautifulSoup(product_page.content,"html.parser")
      product_images=product_soup.find_all("img",class_="q6DClP",src=True)
      model_name=getText(product_soup.find("span",class_="B_NuCI"));
      description=getText(product_soup.find("div",class_="_1mXcCf RmoJUa"));
      img=[image['src'] for image in product_images]
      rating=getText(product_soup.find("div",class_="_3LWZlK"));
      review=getText(product_soup.find("span",class_="_2_R_DZ"));
      original_price=getText(product_soup.find("div",class_="_3I9_wc _2p6lqe"));
      discount_price=getText(product_soup.find("div",class_="_30jeq3 _16Jk6d"));
      discount_percent=getText(product_soup.find("div",class_="_3Ay6Sb _31Dcoz"));
      if not original_price:
          original_price=discount_price;
      li_tooltip=product_soup.find_all("li",class_="_3V2wfe"); 

      getTooltip(li_tooltip,product);
 
      highlights_element=product_soup.find_all("li",class_="_21Ahn-");
      highlights=[h.text.strip() for h in highlights_element];
      table_elements=product_soup.findAll("table",class_="_14cfVK");
      specs={};
      details=getGridData(product_soup);
      if(table_elements):
          for table in table_elements:
             specs.update(getTableData(table));
      product["images"]=(img)
      product["model_name"]=model_name;
      product["description"]=description;
      product["rating"]=rating;
      product["review"]=review;
      product["original_price"]=original_price;
      product["discount_price"]=discount_price;
      product["discount_percent"]=discount_percent;
      product["highlights"]=highlights;
      product["specs"]=specs;
      product["details"]=details;
      return product;


def product_details(url):
  main_page=requests.get(url)
  main_soup = BeautifulSoup(main_page.content, "html.parser")
  product_links=[];
  class1=main_soup.find_all("a",class_="_1fQZEK",href=True);
  class2=main_soup.find_all("a",class_="s1Q9rs",href=True);
  class3=main_soup.find_all("a",class_="_2UzuFa",href=True);
  if(class1):
      product_links = class1;
  elif(class2):
      product_links=class2;
  elif(class3):
      product_links=class3;
  
  with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_link = {executor.submit(process_product, link): link for link in product_links} 
    for future in concurrent.futures.as_completed(future_link):
        link = future_link[future] 
        try:
            product = future.result() 
            data.append(product)
        except Exception as e: 
            print(f"Error processing product {link}: {str(e)}")
 
  next_page=main_soup.find_all("a",class_="_1LKTO3",href=True);
  if(next_page):
        next_link="";
        if(len(next_page)==2):
            if(next_page[1].text == "Next"):
              next_link=next_page[1]["href"];
        else:
            if(next_page[0].text == "Next"):
              next_link=next_page[0]["href"];
        if(next_link):
          next_link=base_url+next_link;
          print(next_link)
          product_details(next_link);
product_details(url);
print(len(data))
f=open("log.json","w");
f.write(json.dumps(data));