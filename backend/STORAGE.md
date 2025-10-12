# Storage Configuration

This application supports two storage backends for uploaded CSV files:

## Local Storage (Default)
- **Use case**: Development, testing, and small deployments
- **Configuration**: Set `STORAGE_TYPE=local` or leave unset
- **Files stored**: In the `data/` directory
- **Pros**: No external dependencies, easy to set up
- **Cons**: Not suitable for production scale

## S3 Storage (Production)
- **Use case**: Production deployments with AWS S3
- **Configuration**: Set `STORAGE_TYPE=s3` and configure AWS credentials
- **Files stored**: In AWS S3 bucket
- **Pros**: Scalable, reliable, cloud-native
- **Cons**: Requires AWS setup and credentials

## Environment Variables

### Required for S3 Storage:
```bash
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

### Optional S3 Configuration:
```bash
S3_BUCKET_NAME=csv-storage-ml
S3_PREFIX=datasets
```

## Switching Storage Backends

1. **For Development/Testing**: Use default (local storage)
2. **For Production**: Set `STORAGE_TYPE=s3` and configure AWS credentials

## Testing

All tests use mock storage and work regardless of the configured backend. The tests will pass whether you're using local or S3 storage.
