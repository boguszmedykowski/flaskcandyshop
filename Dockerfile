FROM python:3.8-slim
WORKDIR /usr/src/app/

# Copy the entire project
COPY . .

# Install Flask and other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 5000

CMD ["python3", "app.py"]
