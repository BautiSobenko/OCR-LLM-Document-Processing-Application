def analyzeDocument(textract_client, file_path):
    return textract_client.analyze_document(
        Document={
            'S3Object': {
                'Bucket': 'textract-console-us-east-2-dcd62a65-0f53-4d08-90bd-90c7bb83ccc7',
                'Name': file_path
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )
