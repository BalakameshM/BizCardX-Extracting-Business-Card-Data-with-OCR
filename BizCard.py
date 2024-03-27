import pymysql
import streamlit as st
from PIL import Image
import os
import cv2
import re
import easyocr
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(layout="wide", page_title="Biz Card", page_icon=":credit_card:", initial_sidebar_state="expanded")
background='''
<style>
[data-testid="stAppViewContainer"]{
        background-color:#b0b1cdb8;   
}
</style>'''
st.markdown(background,unsafe_allow_html=True)
reader = easyocr.Reader(["en"])

db =  pymysql.connect(host = "localhost",
                      user = "root",
                      password = "",
                      database = "pretest")
cursor = db.cursor()

USER_CREDENTIALS = {"admin": "admin123"}

def home_page():
    st.title("BizCardX: Extracting Business Card Data with OCR")
    
    st.image("https://miro.medium.com/v2/da:true/resize:fit:1200/0*STfB20RYe10Xwov7",width=500)
    st.subheader("Overview:")
    st.write("BizCardX transforms business card data management through its intuitive Streamlit GUI and advanced OCR capabilities. Users can effortlessly upload card images, allowing OCR technology to swiftly extract vital details like names, titles, company information, and contact details. The extracted data is seamlessly stored in a SQL database, facilitating easy access, retrieval, and organization.BizCardX empowers users to efficiently manage their contacts, streamline workflows, and drive business growth. With its combination of user-friendly interface, powerful OCR technology, and structured data storage, BizCardX revolutionizes the way business card information is handled, making it an indispensable tool for professionals seeking to optimize their productivity and organization.")
    cursor.execute("SELECT Card_Holder_Name,Designation,Company_Name,Phone_Number,Email,Website,Area,City,State,Pincode FROM card_data")
    updated_df2 = pd.DataFrame(cursor.fetchall(),
                                columns=["Card_Holder_Name","Designation","Company_Name",
        "Phone_Number","Email","Website","Area","City","State","Pincode"])
    st.subheader("Existing Data in Database")
    st.write(updated_df2)

def upload_image():

    file  = st.file_uploader("please chose the file", type=["png","jpg","jpeg"])

    if file!= None:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.image(file,caption='The image has been uploaded successfully',width=500)
        with col2:
            uploaded_cards_dir = os.path.join(os.getcwd(),"bizcard")
            saved_image_path = os.path.join(uploaded_cards_dir, file.name)
            with open(saved_image_path, "wb") as f:
                f.write(file.getbuffer())
            saved_image =  os.getcwd() + "\\" + "bizcard" + "\\" + file.name
            image = cv2.imread(saved_image)
            res = reader.readtext(saved_image)
            preview_image = preview (image,res)
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.pyplot(preview_image)
        
        data = {"Card_Holder_Name":[],
                "Designation":[],
                "Company_Name":[],
                "Phone_Number":[],
                "Email":[],
                "Website":[],
                "Area":[],
                "City":[],
                "State":[],
                "Pincode":[],
                "image": image_to_binary(saved_image)
                }
        get_data(res,data)
        df = pd.DataFrame(data)
        st.success("### Data Extracted!")
        st.write(df)

        if st.button("Upload to Database"):
            for i, row in df.iterrows():
                query1='''insert into card_data(Card_Holder_Name,Designation,Company_Name,
                Phone_Number,Email,Website,Area,City,State,Pincode,Image)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                cursor.execute(query1, tuple(row))
                db.commit()
                cursor.execute('''Select Card_Holder_Name,Designation,Company_Name,
                Phone_Number,Email,Website,Area,City,State,Pincode from card_data''')
                updated_df = pd.DataFrame(cursor.fetchall(),
                columns=["Card Holder Name","Designation","Company Name",
                "Phone Number", "Email","Website", "Area", "City", "State", "Pin_Code"])
                st.success("#### Uploaded to database successfully!")
                st.write(updated_df)

def get_data(res, data):

    card_holder_names = []
    designations = []
    company_names = []
    phone_numbers = []
    emails = []
    websites = []
    areas = []
    cities = []
    states = []
    pincodes = []

    for ind, i in enumerate(res):
        
        if ind == 0:
            card_holder_names.append(i[1])

        elif ind == 1:
            designations.append(i[1])

        elif ind == len(res) - 1:
            company_names.append(i[1])

        elif "www" in i[1].lower():
            websites.append(i[1])
        elif "WWW" in i[1]:
            websites.append(res[ind+1][1] + "." + res[ind+2][1])

        elif "@" in i[1]:
            emails.append(i[1])

        elif "-" in i[1]:
            phone_numbers.append(i[1])
            if len(phone_numbers) == 2:
                phone_numbers = " & ".join(phone_numbers)

        if re.findall('^[0-9].+, [a-zA-Z]+', i[1]):
            areas.append(i[1].split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+', i[1]):
            areas.append(i[1])

        
        match1 = re.findall('.+St , ([a-zA-Z]+).+', i[1])
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i[1])
        match3 = re.findall('^[E].*', i[1])

        if match1:
            cities.append(match1[0])
        elif match2:
            cities.append(match2[0])
        elif match3:
            cities.append(match3[0])

        state_match = re.findall('[a-zA-Z]{9} +[0-9]', i[1])
        if state_match:
            states.append(i[1][:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);', i[1]):
            states.append(i[1].split()[-1])
        if len(states) == 2:
            states.pop(0)

        if len(i[1]) >= 6 and i[1].isdigit():
            pincodes.append(i[1])
        elif re.findall('[a-zA-Z]{9} +[0-9]', i[1]):
            pincodes.append(i[1][10:])

    data["Card_Holder_Name"] = card_holder_names
    data["Designation"] = designations
    data["Company_Name"] = company_names
    data["Phone_Number"] = phone_numbers
    data["Email"] = emails
    data["Website"] = websites
    data["Area"] = areas
    data["City"] = cities
    data["State"] = states
    data["Pincode"] = pincodes
        
def image_to_binary(saved_image):
    with open(saved_image, 'rb') as file:
            binaryData = file.read()
            return binaryData
     
def preview(image,res):
     for (bbox, text, prob) in res:
       
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        cv2.rectangle(image, tl, br, (0, 255, 0), 2)
        cv2.putText(image, text, (tl[0], tl[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        plt.rcParams['figure.figsize'] = (15, 15)
        plt.axis('off')
        plt.imshow(image)

def make_changes():
    st.subheader("make changes")
    cursor.execute("SELECT Card_Holder_Name FROM card_data")
    result = cursor.fetchall()
    business_cards = {}
    for row in result:
        business_cards[row[0]] = row[0]
    options = ["Select Card"] + list(business_cards.keys())
    selected_card = st.selectbox("**Select a card**", options)
    if selected_card == "Select Card":
        st.write("Card not selected")

    else:
        st.markdown("#### Update or modify the data below")
        cursor.execute('''Select Card_Holder_Name,Designation,Company_Name,
        Phone_Number,Email,Website,Area,City,State,Pincode from card_data WHERE Card_Holder_Name=%s''',
        (selected_card,))
        result = cursor.fetchone()
        
        card_holder = st.text_input("card_holder",result[0])
        Designation = st.text_input("Designation",result[1])
        company_name = st.text_input("company_name",result[2])
        Phone_number = st.text_input("Phone_number",result[3])
        Email = st.text_input("Email",result[4])
        website = st.text_input("website",result[5])
        Area = st.text_input("address",result[6])
        city = st.text_input("city",result[7])
        state = st.text_input("state",result[8])
        pincode = st.text_input("pincode",result[9])

        if st.button(":black[Commit changes to DB]"):
                    
                    
                    cursor.execute("""UPDATE card_data SET Card_Holder_Name=%s,Designation=%s,Company_Name=%s,Phone_Number=%s,Email=%s,Website=%s,
                                    Area=%s,City=%s,State=%s,Pincode=%s where Card_Holder_Name=%s""",
                                    (card_holder,Designation,company_name, Phone_number, Email, website, Area, city, state, pincode,
                    selected_card))

                    db.commit()
                    st.success("Information updated in database successfully.")

    if st.button(":black[View data]"):
        cursor.execute('''Select Card_Holder_Name,Designation,Company_Name,
        Phone_Number,Email,Website,Area,City,State,Pincode from card_data''')
        updated_df2 = pd.DataFrame(cursor.fetchall(),
                                columns=["Card_Holder_Name","Designation","Company_Name",
        "Phone_Number","Email","Website","Area","City","State","Pincode"])
        st.write(updated_df2)

def delete():
    st.title("delet")
    cursor.execute("SELECT Card_Holder_Name FROM card_data")
    result = cursor.fetchall()
    business_cards = {}
    for row in result:
        business_cards[row[0]] = row[0]
    options = ["None"] + list(business_cards.keys())
    selected_card = st.selectbox("**Select a card**", options)
    if selected_card == "None":
        st.write("No card selected")
    else:
        st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
        st.write("#### Proceed to delete this card?")
        if st.button("Confirm deletion"):
            cursor.execute(f"DELETE FROM card_data WHERE Card_Holder_Name='{selected_card}'")
            db.commit()
            st.success("Business card information has been deleted from database")

    if st.button(":black[View data]"):
                cursor.execute('''Select Card_Holder_Name,Designation,Company_Name,
                    Phone_Number,Email,Website,Area,City,State,Pincode from card_data''')
                updated_df3 = pd.DataFrame(cursor.fetchall(),
                                            columns=["Card_Holder_Name","Designation","Company_Name",
                    "Phone_Number","Email","Website","Area","City","State","Pincode"])
                st.write(updated_df3)

def login_page():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate_user(username, password):
                st.success("Login successful!")
                st.session_state.authenticated = True
            else:
                st.error("Invalid username or password")
    else:
        st.write("You are already logged in.")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.success("Logout successful.")

    return st.session_state.authenticated

def authenticate_user(username, password):

    return username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password

def main():
        if login_page():
    
            if "Home_page" not in st.session_state:
                st.session_state.Home_page = True
            if "upload_image" not in st.session_state:
                st.session_state.upload_image = False
            if "delete" not in st.session_state:
                st.session_state.delete = False
            if "make_changes" not in st.session_state:
                st.session_state.make_changes = False
            
            if st.sidebar.button("Home"):
                st.session_state.Home_page = True
                st.session_state.upload_image = False
                st.session_state.delete = False
                st.session_state.make_changes = False

            if st.sidebar.button("Upload Image"):
                st.session_state.Home_page = False
                st.session_state.upload_image = True
                st.session_state.delete = False
                st.session_state.make_changes = False

            if st.sidebar.button("Make changes"):
                st.session_state.Home_page = False
                st.session_state.upload_image = False
                st.session_state.delete = False
                st.session_state.make_changes = True

            if st.sidebar.button("Delete"):
                st.session_state.Home_page = False
                st.session_state.upload_image = False
                st.session_state.delete = True
                st.session_state.make_changes = False

            if st.session_state.Home_page:
                home_page()
            elif st.session_state.upload_image:
                upload_image()
            elif st.session_state.make_changes:
                make_changes()
            elif st.session_state.delete:
                delete()

if __name__ == "__main__":
    main()
