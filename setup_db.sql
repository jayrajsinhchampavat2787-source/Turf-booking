-- ==============================================================
-- TURFX: Microsoft SQL Server Database Setup Script
-- Project: TURFX Cricket Turf Booking Management System
-- Database: TURFX_DB
-- ==============================================================
-- You can run this script directly in SQL Server Management Studio (SSMS)
-- or Django will connect automatically using the configured settings.

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TURFX_DB')
BEGIN
    CREATE DATABASE TURFX_DB;
    PRINT 'TURFX_DB database created successfully!';
END
ELSE
BEGIN
    PRINT 'TURFX_DB database already exists.';
END
GO

USE TURFX_DB;
GO

PRINT 'TURFX_DB is active and ready for Django migrations.';
GO
