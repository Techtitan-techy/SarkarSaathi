# Implementation Plan: SarkariSaathi

## Overview

This implementation plan breaks down the SarkariSaathi voice-first AI assistant into discrete coding tasks optimized for a 24-48 hour hackathon timeline. The approach prioritizes core functionality (voice processing, RAG-based eligibility matching, and basic SMS/IVR support) while maintaining the serverless AWS architecture. Tasks are ordered to enable incremental validation and early demonstration of key features.

The implementation uses TypeScript for Lambda functions, AWS CDK for infrastructure as code, and follows AWS serverless best practices for cost optimization and scalability.

## Tasks

- [x] 1. Set up AWS infrastructure foundation and project structure
  - Initialize AWS CDK project with TypeScript
  - Configure AWS region (ap-south-1 Mumbai) and account settings
  - Set up project directory structure: `/lambda`, `/lib`, `/test`, `/data`
  - Install core dependencies: AWS SDK v3, AWS CDK constructs, TypeScript
  - Create base CDK stack with VPC, security groups, and IAM roles
  - Configure environment variables and secrets management with AWS Systems Manager
  - _Requirements: 10.5, 9.2_

- [x] 2. Implement core data models and DynamoDB schema
  - [x] 2.1 Create TypeScript interfaces for core entities
    - Define `UserProfile`, `Demographics`, `Scheme`, `Application`, `Session` interfaces
    - Implement validation functions for each entity type
    - Create utility types for multi-language content and enums
    - _Requirements: 6.1, 6.4_

  - [x] 2.2 Write property test for data model validation
    - **Property 8: User Profile Management**
    - **Validates: Requirements 6.1, 6.2, 6.5**

  - [x] 2.3 Create DynamoDB table definitions with CDK
    - Define Users table with GSI on phoneNumber
    - Define Applications table with GSI on userId and status
    - Define Schemes table with GSI on category and state
    - Define Sessions table with TTL attribute for auto-cleanup
    - Configure on-demand billing mode for cost optimization
    - _Requirements: 6.1, 10.5_

  - [x] 2.4 Implement DynamoDB repository layer
    - Create `UserRepository` with CRUD operations and profile updates
    - Create `SchemeRepository` with filtering and search capabilities
    - Create `ApplicationRepository` with status tracking
    - Implement error handling and retry logic with exponential backoff
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 3. Build voice processing pipeline with Amazon Transcribe and Bhashini
  - [x] 3.1 Implement audio input handler Lambda function
    - Accept audio data from API Gateway (base64 encoded)
    - Validate audio format (MP3, WAV) and size limits
    - Store audio in S3 bucket with lifecycle policies
    - Return S3 presigned URL for processing
    - _Requirements: 1.1, 10.1_

  - [x] 3.2 Create speech-to-text service with language detection
    - Integrate Amazon Transcribe for English and Hindi
    - Implement Bhashini API client for 22+ Indian languages
    - Add language detection logic with confidence scoring
    - Handle background noise filtering and pause detection (3-second threshold)
    - Implement fallback chain: Transcribe → Bhashini → Error with retry prompt
    - _Requirements: 1.1, 1.3, 1.4, 2.1_

  - [x] 3.3 Write property test for speech recognition accuracy
    - **Property 1: Speech Recognition Accuracy**
    - **Validates: Requirements 1.1, 1.3, 1.4**

  - [x] 3.4 Implement text-to-speech service with caching
    - Integrate Amazon Polly for English and Hindi neural voices
    - Implement Bhashini TTS client for regional languages
    - Create S3-based audio cache with 7-day TTL
    - Generate cache keys based on text hash and language
    - Return audio URLs with CloudFront CDN distribution
    - _Requirements: 1.2, 2.1_

  - [x] 3.5 Write property test for TTS quality and multilingual support
    - **Property 2: Multilingual Processing**
    - **Property 3: Text-to-Speech Quality**
    - **Validates: Requirements 1.2, 2.1, 2.2, 2.5**

- [x] 4. Checkpoint - Verify voice pipeline functionality
  - Test end-to-end voice processing with sample audio files
  - Validate language detection and transcription accuracy
  - Ensure audio caching reduces API calls
  - Ensure all tests pass, ask the user if questions arise

- [-] 5. Implement RAG-based eligibility engine with OpenSearch and Bedrock
  - [x] 5.1 Set up Amazon OpenSearch domain and vector store
    - Create OpenSearch domain with t3.small instance (cost-optimized)
    - Configure index mappings for scheme documents with vector fields
    - Set up security policies and VPC access
    - Enable encryption at rest with KMS
    - _Requirements: 9.2, 10.5_

  - [x] 5.2 Create scheme document ingestion pipeline
    - Implement Lambda function to process scheme PDFs from S3
    - Extract text content and metadata from government scheme documents
    - Generate embeddings using Amazon Titan Embeddings
    - Index documents in OpenSearch with metadata (category, state, eligibility)
    - Create sample scheme dataset for hackathon demo (10-15 popular schemes)
    - _Requirements: 3.4, 7.1, 7.5_

  - [x] 5.3 Build eligibility matching service
    - Implement hybrid search combining keyword and semantic matching
    - Create eligibility scoring algorithm based on user demographics
    - Filter schemes by state, category, income, age, occupation
    - Prioritize schemes by benefit amount and application ease
    - Return top 5 matching schemes with confidence scores
    - _Requirements: 3.1, 3.3, 3.5, 4.1_

  - [x] 5.4 Write property test for eligibility assessment
    - **Property 4: Comprehensive Eligibility Assessment**
    - **Property 5: Scheme Categorization and Filtering**
    - **Validates: Requirements 3.1, 3.3, 3.5, 4.1, 4.5**

  - [x] 5.5 Integrate Amazon Bedrock with Claude 3.5 Sonnet
    - Create Bedrock client with Claude 3.5 Sonnet model
    - Implement prompt templates for scheme explanation and eligibility questions
    - Add RAG context injection from OpenSearch results
    - Implement token counting and rate limiting for cost control
    - Handle streaming responses for real-time conversation
    - _Requirements: 3.2, 4.2, 5.2_

  - [x] 5.6 Write unit tests for Bedrock integration
    - Test prompt template generation with various user contexts
    - Test RAG context injection and response quality
    - Test token limiting and cost controls
    - _Requirements: 3.2, 4.2_

- [x] 6. Build conversational AI orchestration with Step Functions
  - [x] 6.1 Design conversation state machine
    - Define states: Welcome, ProfileCollection, SchemeDiscovery, EligibilityCheck, ApplicationGuidance
    - Implement state transitions based on user intent
    - Add error handling and retry logic for each state
    - Configure timeout and fallback paths
    - _Requirements: 3.1, 4.1, 5.1_

  - [x] 6.2 Create conversation manager Lambda function
    - Implement intent classification using Claude
    - Manage conversation context and session state in DynamoDB
    - Handle multi-turn conversations with context retention
    - Implement language switching detection and handling
    - Generate appropriate responses based on current state
    - _Requirements: 2.2, 6.2, 10.1_

  - [x] 6.3 Write unit tests for conversation flow
    - Test state transitions with various user inputs
    - Test context retention across multiple turns
    - Test language switching scenarios
    - _Requirements: 2.2, 6.2_

- [-] 7. Implement SMS/IVR bridge for feature phone support
  - [x] 7.1 Set up Amazon Pinpoint for SMS gateway
    - Create Pinpoint project and configure SMS channel
    - Set up phone number pool for India (+91)
    - Configure message templates for common responses
    - Implement bidirectional SMS handling
    - Add SMS rate limiting and cost controls
    - _Requirements: 8.3, 10.5_

  - [x] 7.2 Create SMS handler Lambda function
    - Parse incoming SMS messages and extract user intent
    - Integrate with conversation manager for response generation
    - Handle multi-part SMS for long responses
    - Implement SMS-specific formatting (160 character chunks)
    - Store SMS conversation history in DynamoDB
    - _Requirements: 8.3, 8.4_

  - [x] 7.3 Set up Amazon Connect for IVR flow
    - Create Connect instance and configure phone number
    - Design IVR flow with DTMF support for basic phones
    - Integrate with Lambda for dynamic responses
    - Implement call recording for quality assurance
    - Configure call queuing and callback system
    - _Requirements: 8.3, 10.2_

  - [x] 7.4 Write integration tests for SMS/IVR flows
    - Test SMS message parsing and response generation
    - Test IVR DTMF navigation
    - Test callback scheduling
    - _Requirements: 8.3_

- [x] 8. Checkpoint - Verify multi-channel functionality
  - Test voice, SMS, and IVR channels independently
  - Validate conversation state persistence across channels
  - Ensure cost controls are working (Free Tier limits)
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Implement application assistance and tracking system
  - [x] 9.1 Create application form handler
    - Parse scheme application requirements from OpenSearch
    - Generate dynamic form fields based on scheme
    - Validate user inputs against scheme criteria
    - Store partial applications with auto-save
    - _Requirements: 5.1, 5.2_

  - [x] 9.2 Build document checklist generator
    - Extract required documents from scheme metadata
    - Generate personalized checklist based on user profile
    - Provide document procurement guidance
    - Track document upload status
    - _Requirements: 5.1, 5.3_

  - [x] 9.3 Implement application submission workflow
    - Create application summary for user review
    - Generate application tracking number
    - Store application in DynamoDB with status tracking
    - Send confirmation SMS with tracking details
    - Implement deadline warnings and reminders
    - _Requirements: 5.4, 5.5, 7.3_

  - [ ] 9.4 Write property test for application completeness
    - **Property 7: Application Process Completeness**
    - **Validates: Requirements 5.1, 5.4, 5.5**

- [ ] 10. Implement security and encryption layer
  - [x] 10.1 Set up AWS KMS for data encryption
    - Create customer-managed KMS keys for different data types
    - Configure key rotation policies
    - Set up key access policies with least privilege
    - _Requirements: 9.2, 6.4_

  - [x] 10.2 Implement encryption for sensitive data
    - Encrypt user profile data in DynamoDB using KMS
    - Encrypt audio files in S3 with SSE-KMS
    - Encrypt application documents with client-side encryption
    - Implement secure key management in Lambda environment
    - _Requirements: 9.2, 9.3, 6.4_

  - [-] 10.3 Write property test for data security
    - **Property 9: Data Security and Encryption**
    - **Validates: Requirements 6.4, 9.2, 9.3**

  - [ ] 10.4 Implement privacy and consent management
    - Create consent collection flow during profile creation
    - Store consent records with timestamps
    - Implement data access request handler
    - Create data deletion workflow with cascade delete
    - _Requirements: 9.1, 9.5, 6.5_

  - [ ] 10.5 Write property test for privacy controls
    - **Property 13: Privacy and Consent Management**
    - **Validates: Requirements 9.1, 9.5**

- [x] 11. Build API Gateway and routing layer
  - [x] 11.1 Create REST API with API Gateway
    - Define API resources: /voice, /sms, /schemes, /applications, /profile
    - Configure request validation and transformation
    - Set up CORS for web interface
    - Implement API key authentication
    - Add request/response logging
    - _Requirements: 10.1, 9.3_

  - [x] 11.2 Implement AWS WAF for API protection
    - Create WAF web ACL with rate limiting rules
    - Add geo-blocking for non-India traffic (optional)
    - Configure SQL injection and XSS protection
    - Set up IP reputation lists
    - _Requirements: 9.2, 10.5_

  - [x] 11.3 Set up CloudFront distribution
    - Create CloudFront distribution for API caching
    - Configure edge locations in India
    - Set up SSL/TLS with ACM certificate
    - Implement cache policies for static content
    - _Requirements: 10.1, 8.4_

- [x] 12. Implement error handling and fallback mechanisms
  - [x] 12.1 Create centralized error handler
    - Define error types and severity levels
    - Implement error logging to CloudWatch
    - Create user-friendly error messages in multiple languages
    - Add error recovery suggestions
    - _Requirements: 1.5, 4.3, 7.4_

  - [x] 12.2 Implement API fallback strategies
    - Add circuit breaker pattern for external API calls
    - Implement exponential backoff for retries
    - Create fallback chain: Primary → Secondary → Cached → Manual
    - Handle government API failures gracefully
    - _Requirements: 7.2, 7.4, 10.4_

  - [x] 12.3 Write property test for error handling
    - **Property 6: Error Handling and Alternatives**
    - **Validates: Requirements 1.5, 4.3, 7.4**

  - [ ] 12.4 Write property test for API integration reliability
    - **Property 10: Government API Integration**
    - **Validates: Requirements 7.1, 7.2, 7.4**

- [ ] 13. Implement monitoring, logging, and alerting
  - [-] 13.1 Set up CloudWatch dashboards
    - Create system health dashboard (Lambda errors, API latency, DynamoDB throttling)
    - Create business metrics dashboard (applications, scheme discoveries, user engagement)
    - Create cost monitoring dashboard with budget alerts
    - Add custom metrics for voice processing accuracy
    - _Requirements: 10.5, 10.2_

  - [ ] 13.2 Configure CloudWatch alarms
    - Set up critical error alarms with SNS notifications
    - Configure performance degradation alerts (response time > 3s)
    - Add cost threshold alarms for budget management
    - Create security event alerts for suspicious activity
    - _Requirements: 10.1, 10.2, 10.5_

  - [ ] 13.3 Implement structured logging
    - Add correlation IDs for request tracing
    - Log user interactions with privacy masking
    - Implement log aggregation and search
    - Set up log retention policies (90 days)
    - _Requirements: 9.4, 10.5_

- [ ] 14. Build accessibility features and offline support
  - [ ] 14.1 Implement text alternatives for hearing impaired
    - Add SMS-based interaction as alternative to voice
    - Provide visual feedback in web interface
    - Create text transcripts of voice conversations
    - _Requirements: 8.1_

  - [ ] 14.2 Add support for slower speech patterns
    - Increase speech recognition timeout to 5 seconds
    - Implement custom speech models for speech impairments
    - Add confirmation prompts for critical inputs
    - _Requirements: 8.2_

  - [ ] 14.3 Implement offline capabilities
    - Cache frequently accessed scheme information in S3
    - Create offline-first SMS responses for common queries
    - Implement sync mechanism when connectivity restored
    - _Requirements: 8.4_

  - [ ] 14.4 Write property test for accessibility support
    - **Property 11: Accessibility Support**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [ ] 15. Checkpoint - Verify security and accessibility
  - Test encryption for all sensitive data
  - Validate accessibility features with different user scenarios
  - Verify error handling and fallback mechanisms
  - Ensure all tests pass, ask the user if questions arise

- [ ] 16. Create sample scheme dataset and seed database
  - [x] 16.1 Prepare government scheme documents
    - Collect 10-15 popular schemes (PM-KISAN, Ayushman Bharat, etc.)
    - Extract eligibility criteria and application procedures
    - Translate scheme information to Hindi and 2-3 regional languages
    - Format documents for OpenSearch ingestion
    - _Requirements: 3.4, 7.1_

  - [x] 16.2 Seed DynamoDB with test data
    - Create sample user profiles with diverse demographics
    - Generate test applications in various states
    - Add sample conversation sessions
    - Create test scheme metadata
    - _Requirements: 6.1, 3.1_

  - [x] 16.3 Index schemes in OpenSearch
    - Run document ingestion pipeline for all schemes
    - Verify vector embeddings are generated correctly
    - Test search functionality with sample queries
    - Validate eligibility matching accuracy
    - _Requirements: 3.1, 7.1_

- [ ] 17. Implement performance optimization and caching
  - [ ] 17.1 Add ElastiCache for session management
    - Set up Redis cluster for session caching
    - Implement session read-through and write-through patterns
    - Configure TTL for session expiration
    - Reduce DynamoDB read load
    - _Requirements: 10.1, 10.5_

  - [ ] 17.2 Optimize Lambda cold starts
    - Implement Lambda layer for shared dependencies
    - Use provisioned concurrency for critical functions
    - Minimize deployment package size
    - Configure appropriate memory allocation
    - _Requirements: 10.1_

  - [ ] 17.3 Implement intelligent caching strategy
    - Cache scheme data with 24-hour TTL
    - Cache audio responses with 7-day TTL
    - Cache eligibility results with 6-hour TTL
    - Implement cache invalidation on scheme updates
    - _Requirements: 10.1, 7.5_

  - [ ] 17.4 Write property test for performance requirements
    - **Property 12: Performance and Reliability**
    - **Validates: Requirements 10.1, 10.2, 10.5**

- [ ] 18. Build web interface for demo and testing
  - [x] 18.1 Create simple React web app
    - Build voice recording interface with browser MediaRecorder API
    - Add text chat interface as fallback
    - Display scheme recommendations with details
    - Show application tracking dashboard
    - _Requirements: 1.1, 3.1, 5.1_

  - [ ] 18.2 Implement web authentication with Cognito
    - Set up Cognito user pool
    - Add sign-up and login flows
    - Integrate with API Gateway authorizer
    - Implement session management
    - _Requirements: 9.2, 6.1_

  - [ ] 18.3 Deploy web app to S3 with CloudFront
    - Build production bundle
    - Upload to S3 bucket with static website hosting
    - Configure CloudFront distribution
    - Set up custom domain (optional)
    - _Requirements: 10.5_

- [ ] 19. Implement automatic scheme update mechanism
  - [ ] 19.1 Create scheme update detector
    - Set up EventBridge rule for daily scheme checks
    - Implement web scraper for government scheme portals
    - Detect new schemes and changes to existing schemes
    - Trigger ingestion pipeline for new schemes
    - _Requirements: 3.4, 7.5_

  - [ ] 19.2 Build user notification system
    - Identify users eligible for new schemes
    - Generate personalized notifications
    - Send SMS alerts for relevant scheme updates
    - Track notification delivery and engagement
    - _Requirements: 7.5_

  - [ ] 19.3 Write property test for automatic updates
    - **Property 14: Automatic Scheme Updates**
    - **Validates: Requirements 3.4, 7.5**

- [ ] 20. Final integration and end-to-end testing
  - [ ] 20.1 Conduct end-to-end testing across all channels
    - Test complete user journey: voice input → scheme discovery → application
    - Validate multi-language support with real audio samples
    - Test SMS and IVR flows with actual phone numbers
    - Verify data persistence and session management
    - _Requirements: All_

  - [ ] 20.2 Run all property-based tests
    - Execute all 14 property tests with 100+ iterations each
    - Document any failures and edge cases discovered
    - Verify all properties hold across random inputs
    - _Requirements: All_

  - [ ] 20.3 Perform load testing
    - Simulate concurrent users (100-500)
    - Test auto-scaling behavior
    - Verify 3-second response time under load
    - Monitor AWS costs during load test
    - _Requirements: 10.1, 10.2, 10.5_

  - [ ] 20.4 Conduct security audit
    - Verify all data encryption is working
    - Test IAM policies and access controls
    - Validate WAF rules and rate limiting
    - Check for exposed secrets or credentials
    - _Requirements: 9.2, 9.3, 9.4_

- [ ] 21. Prepare hackathon demo and documentation
  - [ ] 21.1 Create demo script and test scenarios
    - Prepare 3-5 user personas with different demographics
    - Script demo flow showcasing key features
    - Prepare backup recordings in case of live demo issues
    - Test demo on actual devices (smartphone, feature phone)
    - _Requirements: All_

  - [ ] 21.2 Generate architecture diagrams and documentation
    - Create system architecture diagram
    - Document API endpoints and request/response formats
    - Write deployment guide for judges
    - Prepare cost analysis and scalability report
    - _Requirements: 10.5_

  - [ ] 21.3 Create presentation materials
    - Build slide deck highlighting problem, solution, impact
    - Include live demo videos as backup
    - Prepare technical deep-dive for Q&A
    - Document social impact and reach potential
    - _Requirements: All_

- [ ] 22. Final checkpoint - Production readiness
  - Verify all core features are working end-to-end
  - Ensure monitoring and alerting are configured
  - Validate cost optimization measures are in place
  - Confirm security best practices are implemented
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery within hackathon timeline
- Focus on tasks 1-8 for core functionality demo (voice processing + eligibility matching)
- Tasks 9-15 add production-ready features (security, monitoring, accessibility)
- Tasks 16-21 are for polish, optimization, and demo preparation
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from design document
- Checkpoints ensure incremental validation and provide natural break points
- Prioritize working demo over comprehensive testing during hackathon
- Use AWS Free Tier limits as guardrails throughout implementation
