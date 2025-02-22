#Deriving the latest base image
FROM python:latest

#Labels as key value pair
LABEL Maintainer="dgoins2019@fau.edu"

# Set the working directory
WORKDIR /src

# Copy the rest of the application code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python", "bot-1.py"]
# To run retire.js separately, uncomment the following line
# CMD ["retire", "--outputformat", "json", "--outputpath", "/app/retire_report.json"]