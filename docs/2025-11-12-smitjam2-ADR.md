# ADR-001: Use Google Cloud Storage buckets for the main file storage

**Status:** Accepted

**Context:**
We need a reliable, scalable file storage system for our unstructured, user uploaded files. Requirements include fast access, fast READ/WRITE, and a pleasant user experience. Must be hosted on GCP

**Decision:**
We will use Google Cloud Storage Buckets as the primary storage bucket for the project.

**Options Considered:**
- S3 Buckets (AWS)
- MinIO (Self-hosted / Open Source)

**Rationale:**
Google Cloud Storage is the native and preferred storage solution within the Google Cloud Platform (GCP), offering superior integration and lower latency compared to cross-cloud options like AWS S3.

**Consequences:**
- Dependency on GCP: The project is now tightly coupled with Google Cloud Storage for file hosting. Future migration to another cloud provider will require a significant effort to transfer data and update APIs.
- IAM Management: We must carefully manage Identity and Access Management (IAM) policies on the buckets to ensure secure access control for user files.
- Client Libraries: We will use the official Google Cloud Storage client libraries in our application's backend services (e.g., for Python or Node.js).
- Cost Monitoring: We must implement monitoring and alerts for storage and network usage to manage operational costs effectively.
  
**References:**
[Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
[GCP Pricing Calculator](https://cloud.google.com/products/calculator?hl=en)
Internal Infrastructure Review Notes (2025-11-05)
