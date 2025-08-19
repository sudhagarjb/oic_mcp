# CL_AR_INVOICE_DB_SAAS_APP_INTG Integration Analysis

## Overview
**Integration Name**: CL_AR_INVOICE_DB_SAAS_APP_INTG  
**Version**: 01.00.0041  
**Status**: ACTIVATED  
**Pattern**: Orchestration  
**Description**: AR Invoice Creation and application Integration with Omni Channel receipts/CM(New Version1)  
**Package**: XXCL_OIC_INTEGRATION_PKG  

## Integration Architecture

### Trigger (Source)
- **Connection**: CL_REST_CONN
- **Type**: REST API
- **Role**: SOURCE
- **Purpose**: Receives invoice creation requests via REST API

### Target Connections (79 endpoints total)

#### 1. Database Operations (CL_ATP_DB_CONN - Oracle ATP)
**Primary Database**: Oracle Autonomous Transaction Processing (ATP)  
**Host**: hfttrfwt.adb.ap-mumbai-1.oraclecloud.com  
**Service**: caratlaneoicatptest_medium  
**SID**: CARATLANEOICATPTEST  

**Key Database Operations**:
- `InvokeUpdatePackage` - Package updates
- `GetInvoiceHeaderData` - Retrieve invoice header information
- `GetInvoiceLineData` - Retrieve invoice line details
- `UpdateInvoiceLineID` - Update invoice line identifiers
- `GetActivityApplicationDtl` - Get application activity details
- `UpdateStatusInHDR` - Update header status
- `GenerateResponse` - Generate response data
- `InsertInvoiceHeaderData` - Insert new invoice headers
- `UpdateLineDFF` - Update descriptive flexfield data
- `InsertTaxData` - Insert tax information
- `InsertLineDetailsTbl` - Insert line details
- `CallUpdateTaxdetailsProc` - Tax detail procedures
- `InvokeInvoiceNumUpdateProc` - Invoice number updates
- `UpdateErrorMessage` - Error message updates
- `GetLineData` - Retrieve line data
- `CallOrderTypeProc` - Order type processing
- `GetOrderNumber` - Retrieve order numbers
- `InsertPickWaveDetails` - Pick wave details
- `UpdateApplicationStatus` - Application status updates
- `InsertShipmentNumber` - Shipment number insertion
- `CheckRetryStatus` - Retry status checks
- `GetInvoiceDetails` - Invoice detail retrieval
- `UpdateInvoiceCompletion` - Invoice completion updates
- `UpdatePickWaveLines` - Pick wave line updates
- `UpdateShipmentLines` - Shipment line updates
- `UpdatePriceTbl` - Price table updates
- `GetOmniChannelReceiptsCM` - Omni channel receipt retrieval
- `getTrxDetails` - Transaction details
- `GetReceiptSeqID` - Receipt sequence IDs
- `GetPaymentMethod` - Payment method retrieval
- `getFranchiseBillToDetails` - Franchise billing details
- `getFranchisePartyName` - Franchise party names
- `GetOrderHeaderID` - Order header IDs
- `GetReceiptCMIds` - Receipt credit memo IDs
- `GetInvoiceOrg` - Invoice organization data
- `GetSourceOrderBUDetails` - Source order business unit details
- `UPDATECROSSRECEIPTDTLS` - Cross receipt detail updates
- `GetFranchiseCustomerDetails` - Franchise customer details
- `GetTargetFranchiseDetails` - Target franchise details
- `UpdateCMDetails` - Credit memo detail updates
- `GetCrossBUReceiptDetails` - Cross business unit receipt details
- `GetMaskedAccountPOPTOPOC` - Masked account data
- `GetReceiptFranchiseDetail` - Receipt franchise details

#### 2. ERP System Integration (CL_ERP_REST_CONN)
**Type**: REST API  
**Purpose**: Integration with Oracle ERP system

**Key ERP Operations**:
- `CreateCustomerInvoice` - Create customer invoices in ERP
- `GetInvoiceHDR` - Retrieve invoice headers from ERP
- `GetInvoiceDFF` - Get descriptive flexfield data
- `GetLinesDetails` - Retrieve line details
- `GetLineDFFDetails` - Get line descriptive flexfield details
- `GetTaxInvoiceLine` - Retrieve tax invoice lines
- `CreatePickWave` - Create pick waves
- `ConfirmShipment` - Confirm shipments
- `GetShipmentDetails` - Retrieve shipment details
- `DelinkCreditMemo` - Remove credit memo links
- `DelinkReceipt` - Remove receipt links
- `CreateCrossBUReceipt` - Create cross business unit receipts
- `CreateCrossReceiptLink` - Create cross receipt links
- `CreateCreditMemo` - Create credit memos
- `CreateCreditMemoforFranchise` - Create franchise credit memos
- `CreateCreditMemoForPOPOG` - Create POP credit memos
- `CreateReceiptPOP` - Create POP receipts
- `LinkPoPReceipt` - Link POP receipts
- `LinkCM` - Link credit memos
- `GetCustomerPartyNumber` - Retrieve customer party numbers
- `GetCMDFF` - Get credit memo descriptive flexfield data
- `GetCrossBUReceiptDetails` - Cross business unit receipt details

#### 3. SOAP Services (CL_STANDA_RECEIP_SOAP_CONN)
**Type**: SOAP Web Service  
**Purpose**: Standard receipt processing

**Operations**:
- `ProcessApplyReceipt` - Process receipt applications
- `ReceiptWriteOff` - Receipt write-off processing

#### 4. Credit Memo Processing (CL_CREDIT_MEMO_CONN)
**Type**: Specialized connection for credit memo operations

**Operations**:
- `CreditMemoApply` - Apply credit memos

#### 5. Debit Memo Processing (CL_DEBIT_MEMO_CONN)
**Type**: Specialized connection for debit memo operations

**Operations**:
- `CreateDebitMemo` - Create debit memos
- `CreateDebitMemoForFranchisee` - Create franchise debit memos

#### 6. Adjustment Processing (CL_ADJUSTMENT_CONN)
**Type**: Specialized connection for adjustments

**Operations**:
- `CreateCMAdjustment` - Create credit memo adjustments

#### 7. Descriptive Flexfield Updates (CL_AR_DFF_UPDATE_CONN)
**Type**: Specialized connection for DFF updates

**Operations**:
- `UpdateDMDFF` - Update debit memo descriptive flexfields
- `DebitMemoDFFUpdate` - Debit memo DFF updates

#### 8. Streaming Services (CL_OCI_STREAMIN_CONN)
**Type**: Oracle Cloud Infrastructure Streaming

**Operations**:
- `PublishInvoiceKafka` - Publish invoice data to Kafka
- `PublishErrorMessage` - Publish error messages

#### 9. Error Notification (PRESEEDED_COLLOCATED_CONN_1741)
**Type**: Built-in error notification service

**Operations**:
- `CallErrorNotificationIntg` - Call error notification integration

## Integration Flow Analysis

### Primary Business Process
This integration handles the complete lifecycle of AR (Accounts Receivable) invoice processing:

1. **Invoice Creation**: Receives invoice creation requests via REST API
2. **Data Retrieval**: Fetches invoice header and line data from ERP system
3. **Database Operations**: Stores and manages invoice data in ATP database
4. **Receipt Processing**: Handles Omni Channel receipts and credit memos
5. **Cross-Business Unit Processing**: Manages cross-business unit receipts
6. **Franchise Operations**: Specialized processing for franchise customers
7. **Tax Processing**: Handles tax calculations and updates
8. **Shipment Integration**: Integrates with shipping and pick wave processes
9. **Error Handling**: Comprehensive error notification and logging
10. **Event Publishing**: Publishes events to streaming services for real-time processing

### Key Features
- **Multi-System Integration**: Connects ERP, Database, and external systems
- **Real-time Processing**: Uses streaming services for event-driven architecture
- **Error Resilience**: Comprehensive error handling and retry mechanisms
- **Scalability**: Uses Oracle ATP for high-performance database operations
- **Audit Trail**: Tracks all operations with detailed logging
- **Flexibility**: Supports descriptive flexfields for custom attributes

### Technical Architecture
- **Orchestration Pattern**: Centralized flow control
- **REST APIs**: Modern API-based integration
- **Database Integration**: Direct database operations for performance
- **SOAP Services**: Legacy system integration where needed
- **Event Streaming**: Real-time event publishing
- **Security**: SSL/TLS encryption and authentication

## Connection Details

### REST Connection (CL_REST_CONN)
- **Base URL**: https://caratlane-oic-test-bmdzqmmqkmi3-bo.integration.ap-mumbai-1.ocp.oraclecloud.com/
- **Security**: Basic Authentication
- **Usage**: 287 total, 70 active

### ATP Database Connection (CL_ATP_DB_CONN)
- **Host**: hfttrfwt.adb.ap-mumbai-1.oraclecloud.com
- **Port**: 1522
- **Service**: caratlaneoicatptest_medium
- **Security**: JDBC over SSL with wallet authentication
- **Usage**: 793 total, 339 active

## Tracking Variables
- **Primary**: cl_invoice_ref_number
- **Secondary**: tracking_var_2, tracking_var_3

## Integration Complexity
- **Total Endpoints**: 79
- **Connection Types**: 9 different connection types
- **Database Operations**: 40+ database operations
- **ERP Operations**: 20+ ERP system operations
- **Specialized Processing**: Credit memos, debit memos, adjustments, DFF updates

This integration represents a comprehensive AR invoice management system that handles complex business processes across multiple systems with robust error handling and real-time event processing capabilities. 