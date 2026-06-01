import uvicorn

if __name__ == "__main__":
    # प्रोडक्शन ग्रेड री-लोडिंग सर्वर
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
  q
