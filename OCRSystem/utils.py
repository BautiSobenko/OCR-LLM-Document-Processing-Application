def analyzeDocument(textract_client, file_path):
    return textract_client.analyze_document(
        Document={
            'S3Object': {
                'Bucket': 'myawsbucketocrrecognition',
                'Name': file_path
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )
