FROM python:3.7

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000/tcp
ENV FLASK_CONFIG=production
ENTRYPOINT ["python"]
CMD ["wsgi.py"]
