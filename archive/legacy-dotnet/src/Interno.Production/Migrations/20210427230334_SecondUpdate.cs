using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

namespace Interno.Production.Migrations
{
    public partial class SecondUpdate : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Autority",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Autority", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "BloodType",
                columns: table => new
                {
                    Group = table.Column<string>(maxLength: 3, nullable: false),
                    Donate = table.Column<string>(nullable: true),
                    Receive = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BloodType", x => x.Group);
                });

            migrationBuilder.CreateTable(
                name: "BreakType",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BreakType", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "BusinessUnit",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BusinessUnit", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Contract",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 10, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    Days = table.Column<int>(nullable: false),
                    Active = table.Column<bool>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Contract", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Department",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Department", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Issue",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Type = table.Column<int>(nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: false),
                    Status = table.Column<bool>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Issue", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "LaborType",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 100, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_LaborType", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Partnership",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 15, nullable: false),
                    Name = table.Column<string>(nullable: false),
                    Type = table.Column<int>(nullable: false),
                    Status = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Partnership", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "ProductCategory",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductCategory", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Rout",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Guid = table.Column<Guid>(nullable: false),
                    Code = table.Column<string>(maxLength: 13, nullable: true),
                    Name = table.Column<string>(maxLength: 100, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    Revision = table.Column<string>(maxLength: 5, nullable: false),
                    Target = table.Column<string>(maxLength: 25, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Rout", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Shift",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 13, nullable: false),
                    Start = table.Column<TimeSpan>(nullable: false),
                    End = table.Column<TimeSpan>(nullable: false),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    AvailableTime = table.Column<TimeSpan>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Shift", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "UM",
                columns: table => new
                {
                    Code = table.Column<string>(maxLength: 4, nullable: false),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Plural = table.Column<string>(maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UM", x => x.Code);
                });

            migrationBuilder.CreateTable(
                name: "User",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Username = table.Column<string>(nullable: true),
                    Password = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_User", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "WarehouseGroup",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 25, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WarehouseGroup", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "WarehouseType",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 25, nullable: false),
                    Decription = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WarehouseType", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Person",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LastNamePat = table.Column<string>(maxLength: 25, nullable: false),
                    LastNameMat = table.Column<string>(maxLength: 25, nullable: true),
                    FirstName = table.Column<string>(maxLength: 25, nullable: false),
                    MiddleName = table.Column<string>(maxLength: 25, nullable: true),
                    PrettyName = table.Column<string>(maxLength: 150, nullable: true),
                    SSN = table.Column<string>(maxLength: 50, nullable: true),
                    RFC = table.Column<string>(maxLength: 50, nullable: true),
                    CURP = table.Column<string>(maxLength: 50, nullable: true),
                    Birthday = table.Column<DateTime>(nullable: false),
                    Nationality = table.Column<string>(maxLength: 25, nullable: true),
                    Birthplace = table.Column<string>(maxLength: 25, nullable: true),
                    Gender = table.Column<int>(nullable: false),
                    Height = table.Column<float>(nullable: false),
                    Weight = table.Column<float>(nullable: false),
                    RelationshipStatus = table.Column<int>(nullable: false),
                    Childrens = table.Column<int>(nullable: false),
                    BloodTypeGroup = table.Column<string>(nullable: true),
                    Religion = table.Column<string>(maxLength: 25, nullable: true),
                    Passport = table.Column<bool>(nullable: false),
                    Visa = table.Column<bool>(nullable: false),
                    Sentry = table.Column<bool>(nullable: false),
                    GlobalEntry = table.Column<bool>(nullable: false),
                    TravelAvailability = table.Column<bool>(nullable: false),
                    Relocation = table.Column<bool>(nullable: false),
                    AboutMe = table.Column<string>(maxLength: 250, nullable: true),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    Suspended = table.Column<bool>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Person", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Person_BloodType_BloodTypeGroup",
                        column: x => x.BloodTypeGroup,
                        principalTable: "BloodType",
                        principalColumn: "Group",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Item",
                columns: table => new
                {
                    Guid = table.Column<Guid>(nullable: false),
                    Code = table.Column<string>(maxLength: 45, nullable: false),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: false),
                    CategoryId = table.Column<int>(nullable: true),
                    Alias = table.Column<string>(maxLength: 45, nullable: true),
                    Active = table.Column<bool>(nullable: false),
                    Revision = table.Column<string>(maxLength: 5, nullable: true),
                    Status = table.Column<int>(nullable: false),
                    Weight = table.Column<float>(nullable: false),
                    Length = table.Column<float>(nullable: false),
                    Width = table.Column<float>(nullable: false),
                    Height = table.Column<float>(nullable: false),
                    MinOrderQty = table.Column<float>(nullable: false),
                    MaxOrderQty = table.Column<float>(nullable: false),
                    SafetyStock = table.Column<float>(nullable: false),
                    ReorderPoint = table.Column<float>(nullable: false),
                    OrderMultiple = table.Column<float>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Item", x => new { x.Guid, x.Code });
                    table.ForeignKey(
                        name: "FK_Item_ProductCategory_CategoryId",
                        column: x => x.CategoryId,
                        principalTable: "ProductCategory",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "breaksGroups",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    ShiftId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_breaksGroups", x => x.Id);
                    table.ForeignKey(
                        name: "FK_breaksGroups_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "RefreshToken",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Token = table.Column<string>(nullable: true),
                    Expires = table.Column<DateTime>(nullable: false),
                    Created = table.Column<DateTime>(nullable: false),
                    CreatedByIp = table.Column<string>(nullable: true),
                    Revoked = table.Column<DateTime>(nullable: true),
                    RevokedByIp = table.Column<string>(nullable: true),
                    RevokedByToken = table.Column<string>(nullable: true),
                    UserId = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RefreshToken", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RefreshToken_User_UserId",
                        column: x => x.UserId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Address",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Type = table.Column<int>(nullable: false),
                    AddressLine1 = table.Column<string>(maxLength: 250, nullable: false),
                    AddressLine2 = table.Column<string>(maxLength: 250, nullable: true),
                    City = table.Column<string>(maxLength: 45, nullable: false),
                    ZipCode = table.Column<int>(nullable: false),
                    State = table.Column<string>(maxLength: 100, nullable: false),
                    Country = table.Column<string>(maxLength: 100, nullable: false),
                    Region = table.Column<string>(maxLength: 100, nullable: true),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Address", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Address_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "License",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LicenseName = table.Column<string>(maxLength: 100, nullable: false),
                    Type = table.Column<string>(maxLength: 25, nullable: false),
                    Number = table.Column<string>(maxLength: 100, nullable: true),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_License", x => x.Id);
                    table.ForeignKey(
                        name: "FK_License_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Break",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 15, nullable: false),
                    Start = table.Column<TimeSpan>(nullable: false),
                    End = table.Column<TimeSpan>(nullable: false),
                    TypeId = table.Column<int>(nullable: false),
                    Duration = table.Column<TimeSpan>(nullable: false),
                    BreaksGroupId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Break", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Break_breaksGroups_BreaksGroupId",
                        column: x => x.BreaksGroupId,
                        principalTable: "breaksGroups",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Break_BreakType_TypeId",
                        column: x => x.TypeId,
                        principalTable: "BreakType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Location",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    AddressId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Location", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Location_Address_AddressId",
                        column: x => x.AddressId,
                        principalTable: "Address",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Facility",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 25, nullable: false),
                    Name = table.Column<string>(maxLength: 100, nullable: false),
                    LocationId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Facility", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Facility_Location_LocationId",
                        column: x => x.LocationId,
                        principalTable: "Location",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Area",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    Discriminator = table.Column<string>(nullable: false),
                    FacilityId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Area", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Area_Facility_FacilityId",
                        column: x => x.FacilityId,
                        principalTable: "Facility",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "JobPosition",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 250, nullable: false),
                    DepartmentId = table.Column<int>(nullable: false),
                    AreaId = table.Column<int>(nullable: true),
                    AutorityId = table.Column<int>(nullable: true),
                    SalaryRangeFrom = table.Column<double>(nullable: false),
                    SalaryRangeOut = table.Column<double>(nullable: false),
                    Objetive = table.Column<string>(nullable: true),
                    Created = table.Column<DateTime>(nullable: false),
                    Updated = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_JobPosition", x => x.Id);
                    table.ForeignKey(
                        name: "FK_JobPosition_Area_AreaId",
                        column: x => x.AreaId,
                        principalTable: "Area",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_JobPosition_Autority_AutorityId",
                        column: x => x.AutorityId,
                        principalTable: "Autority",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_JobPosition_Department_DepartmentId",
                        column: x => x.DepartmentId,
                        principalTable: "Department",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Warehouse",
                columns: table => new
                {
                    Code = table.Column<string>(maxLength: 13, nullable: false),
                    Name = table.Column<string>(maxLength: 100, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    TypeId = table.Column<int>(nullable: false),
                    Capacity = table.Column<float>(nullable: false),
                    UnitCode = table.Column<string>(maxLength: 4, nullable: true),
                    GroupId = table.Column<int>(nullable: true),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    DeleteDate = table.Column<DateTime>(nullable: false),
                    Delete = table.Column<bool>(nullable: false),
                    Active = table.Column<bool>(type: "TINYINT(1)", nullable: false),
                    Discriminator = table.Column<string>(nullable: false),
                    FacilityId = table.Column<int>(nullable: true),
                    BreakGroupId = table.Column<int>(nullable: true),
                    AreaId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Warehouse", x => x.Code);
                    table.ForeignKey(
                        name: "FK_Warehouse_Facility_FacilityId",
                        column: x => x.FacilityId,
                        principalTable: "Facility",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Warehouse_WarehouseGroup_GroupId",
                        column: x => x.GroupId,
                        principalTable: "WarehouseGroup",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Warehouse_WarehouseType_TypeId",
                        column: x => x.TypeId,
                        principalTable: "WarehouseType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Warehouse_UM_UnitCode",
                        column: x => x.UnitCode,
                        principalTable: "UM",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Warehouse_Area_AreaId",
                        column: x => x.AreaId,
                        principalTable: "Area",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Warehouse_breaksGroups_BreakGroupId",
                        column: x => x.BreakGroupId,
                        principalTable: "breaksGroups",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Employee",
                columns: table => new
                {
                    Number = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Id = table.Column<Guid>(nullable: false),
                    PersonId = table.Column<int>(nullable: false),
                    Active = table.Column<bool>(nullable: false),
                    PositionId = table.Column<int>(nullable: false),
                    ShiftId = table.Column<int>(nullable: false),
                    ContractId = table.Column<int>(nullable: true),
                    BusinessUnitId = table.Column<int>(nullable: true),
                    SupervisorNumber = table.Column<int>(nullable: false),
                    ManagerNumber = table.Column<int>(nullable: false),
                    DirectorNumber = table.Column<int>(nullable: false),
                    Direct = table.Column<bool>(nullable: false),
                    Hourly = table.Column<bool>(nullable: false),
                    Created = table.Column<DateTime>(nullable: false),
                    Updated = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Employee", x => x.Number);
                    table.ForeignKey(
                        name: "FK_Employee_BusinessUnit_BusinessUnitId",
                        column: x => x.BusinessUnitId,
                        principalTable: "BusinessUnit",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Employee_Contract_ContractId",
                        column: x => x.ContractId,
                        principalTable: "Contract",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Employee_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Employee_JobPosition_PositionId",
                        column: x => x.PositionId,
                        principalTable: "JobPosition",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Employee_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "OperationTime",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Guid = table.Column<Guid>(nullable: false),
                    Keying = table.Column<int>(nullable: false),
                    Product = table.Column<string>(nullable: false),
                    Description = table.Column<string>(nullable: false),
                    WarehouseCode = table.Column<string>(nullable: true),
                    Operation = table.Column<string>(nullable: false),
                    Operators = table.Column<int>(nullable: false),
                    WorkControl = table.Column<string>(maxLength: 100, nullable: true),
                    RunTime = table.Column<TimeSpan>(nullable: false),
                    SetTime = table.Column<TimeSpan>(nullable: false),
                    LMPU = table.Column<double>(nullable: false),
                    Inprovement = table.Column<double>(nullable: false),
                    OffSet = table.Column<decimal>(nullable: false),
                    Repeat = table.Column<int>(nullable: false),
                    Cost = table.Column<decimal>(nullable: false),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Username = table.Column<string>(maxLength: 100, nullable: true),
                    RoutId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_OperationTime", x => x.Id);
                    table.ForeignKey(
                        name: "FK_OperationTime_Rout_RoutId",
                        column: x => x.RoutId,
                        principalTable: "Rout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_OperationTime_Warehouse_WarehouseCode",
                        column: x => x.WarehouseCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Plannings",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Line = table.Column<string>(nullable: false),
                    PartNumber = table.Column<string>(nullable: false),
                    OperationTimeId = table.Column<int>(nullable: true),
                    Order = table.Column<string>(nullable: true),
                    OrderQty = table.Column<int>(nullable: false),
                    ShippingDate = table.Column<DateTime>(nullable: false),
                    SO = table.Column<string>(nullable: true),
                    SOLine = table.Column<string>(nullable: true),
                    PO = table.Column<string>(nullable: true),
                    altBOM = table.Column<string>(nullable: true),
                    KitDate = table.Column<DateTime>(nullable: false),
                    Status = table.Column<int>(nullable: false),
                    WHSUpdate = table.Column<DateTime>(nullable: false),
                    Employee = table.Column<string>(nullable: true),
                    ReceivedDate = table.Column<DateTime>(nullable: false),
                    EmployeeReceived = table.Column<string>(nullable: true),
                    Comments = table.Column<string>(nullable: true),
                    Comments2 = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Plannings", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Plannings_OperationTime_OperationTimeId",
                        column: x => x.OperationTimeId,
                        principalTable: "OperationTime",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Tracking",
                columns: table => new
                {
                    Reference = table.Column<string>(nullable: false),
                    ResourceId = table.Column<int>(nullable: false),
                    ResourceCode = table.Column<string>(nullable: true),
                    OperationTimeId = table.Column<int>(nullable: false),
                    Item = table.Column<string>(nullable: true),
                    Alias = table.Column<string>(nullable: true),
                    Series = table.Column<string>(nullable: true),
                    Sheet = table.Column<string>(nullable: true),
                    TrackingNumber = table.Column<string>(nullable: true),
                    Qty = table.Column<decimal>(nullable: false),
                    Responsible = table.Column<string>(maxLength: 100, nullable: true),
                    Target = table.Column<string>(maxLength: 100, nullable: true),
                    Cost = table.Column<decimal>(type: "decimal(16, 4)", nullable: false),
                    Comment = table.Column<string>(maxLength: 250, nullable: true),
                    Start = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    StartEmployeeNumber = table.Column<int>(nullable: true),
                    Close = table.Column<DateTime>(nullable: false),
                    CloseEmployeeNumber = table.Column<int>(nullable: true),
                    Reject = table.Column<DateTime>(nullable: false),
                    RejectEmployeeNumber = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.ForeignKey(
                        name: "FK_Tracking_Employee_CloseEmployeeNumber",
                        column: x => x.CloseEmployeeNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Tracking_OperationTime_OperationTimeId",
                        column: x => x.OperationTimeId,
                        principalTable: "OperationTime",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Tracking_Employee_RejectEmployeeNumber",
                        column: x => x.RejectEmployeeNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Tracking_Warehouse_ResourceCode",
                        column: x => x.ResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Tracking_Employee_StartEmployeeNumber",
                        column: x => x.StartEmployeeNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "WorkOrder",
                columns: table => new
                {
                    Id = table.Column<string>(nullable: false),
                    Guid = table.Column<Guid>(nullable: false),
                    Type = table.Column<int>(nullable: false),
                    FinishItemCode = table.Column<string>(nullable: false),
                    OperationTimeId = table.Column<int>(nullable: true),
                    Alias = table.Column<string>(maxLength: 45, nullable: true),
                    UMCode = table.Column<string>(maxLength: 4, nullable: true),
                    OrderQty = table.Column<int>(nullable: false),
                    ManufQty = table.Column<int>(nullable: false),
                    Status = table.Column<int>(nullable: false),
                    MaterialStatus = table.Column<int>(nullable: false),
                    Review = table.Column<string>(maxLength: 5, nullable: true),
                    Lot = table.Column<long>(nullable: false),
                    Cost = table.Column<double>(nullable: false),
                    Request = table.Column<DateTime>(nullable: false),
                    Start = table.Column<DateTime>(nullable: false),
                    Finish = table.Column<DateTime>(nullable: false),
                    Trascurred = table.Column<TimeSpan>(nullable: false),
                    Downtime = table.Column<TimeSpan>(nullable: false),
                    EstimatedTime = table.Column<TimeSpan>(nullable: false),
                    EstimatedCost = table.Column<double>(nullable: false),
                    Approved = table.Column<bool>(nullable: false),
                    Responsible = table.Column<string>(maxLength: 100, nullable: true),
                    Target = table.Column<string>(maxLength: 100, nullable: true),
                    Planner = table.Column<string>(maxLength: 100, nullable: true),
                    Comment = table.Column<string>(nullable: true),
                    Affected = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    RoutId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WorkOrder", x => x.Id);
                    table.ForeignKey(
                        name: "FK_WorkOrder_OperationTime_OperationTimeId",
                        column: x => x.OperationTimeId,
                        principalTable: "OperationTime",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_WorkOrder_Rout_RoutId",
                        column: x => x.RoutId,
                        principalTable: "Rout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_WorkOrder_UM_UMCode",
                        column: x => x.UMCode,
                        principalTable: "UM",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Results",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Priority = table.Column<int>(nullable: false),
                    Date = table.Column<DateTime>(nullable: false),
                    ResourceCode = table.Column<string>(nullable: false),
                    SubResourceCode = table.Column<string>(nullable: true),
                    ShiftId = table.Column<int>(nullable: false),
                    BreaksId = table.Column<int>(nullable: true),
                    Operators = table.Column<int>(nullable: false),
                    LeadTime = table.Column<TimeSpan>(nullable: false),
                    InitialTime = table.Column<DateTime>(nullable: false),
                    AvailableTime = table.Column<TimeSpan>(nullable: false),
                    ScheduledStops = table.Column<TimeSpan>(nullable: false),
                    ProductiveTime = table.Column<TimeSpan>(nullable: false),
                    ScheduledOperatingTime = table.Column<TimeSpan>(nullable: false),
                    OperativeTime = table.Column<TimeSpan>(nullable: false),
                    OverTimeEnd = table.Column<DateTime>(nullable: false),
                    OverTime = table.Column<TimeSpan>(nullable: false),
                    Item = table.Column<string>(nullable: true),
                    Description = table.Column<string>(nullable: true),
                    WorkOrder = table.Column<string>(nullable: true),
                    OrderQty = table.Column<int>(nullable: false),
                    PlanQty = table.Column<int>(nullable: false),
                    Actual = table.Column<int>(nullable: false),
                    Rate = table.Column<double>(nullable: false),
                    OEE = table.Column<double>(nullable: false),
                    OE = table.Column<double>(nullable: false),
                    TEP = table.Column<double>(nullable: false),
                    Availability = table.Column<double>(nullable: false),
                    Eficiency = table.Column<double>(nullable: false),
                    FirstPassYield = table.Column<double>(nullable: false),
                    OEE1 = table.Column<double>(nullable: false),
                    TakTime = table.Column<TimeSpan>(nullable: false),
                    Capacity = table.Column<double>(nullable: false),
                    LMPU = table.Column<double>(nullable: false),
                    Inprovement = table.Column<double>(nullable: false),
                    ShippingDate = table.Column<DateTime>(nullable: false),
                    WHSDate = table.Column<DateTime>(nullable: false),
                    SMKTDate = table.Column<DateTime>(nullable: false),
                    Date1 = table.Column<DateTime>(nullable: false),
                    Date2 = table.Column<DateTime>(nullable: false),
                    LeaderNumber = table.Column<int>(nullable: false),
                    SupervisorNumber = table.Column<int>(nullable: false),
                    Planner = table.Column<string>(nullable: true),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    WorkOrderId = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Results", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Results_breaksGroups_BreaksId",
                        column: x => x.BreaksId,
                        principalTable: "breaksGroups",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Results_Warehouse_ResourceCode",
                        column: x => x.ResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Results_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Results_Warehouse_SubResourceCode",
                        column: x => x.SubResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Results_WorkOrder_WorkOrderId",
                        column: x => x.WorkOrderId,
                        principalTable: "WorkOrder",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Downtime",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Guid = table.Column<Guid>(nullable: false),
                    IssueId = table.Column<int>(nullable: false),
                    ResultId = table.Column<int>(nullable: false),
                    RequestNumber = table.Column<int>(nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: false),
                    Status = table.Column<int>(nullable: false),
                    AssignToNumber = table.Column<int>(nullable: true),
                    Action = table.Column<string>(maxLength: 250, nullable: true),
                    CommitDate = table.Column<DateTime>(nullable: false),
                    ClosedDate = table.Column<DateTime>(nullable: false),
                    Escalation = table.Column<DateTime>(nullable: false),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Downtime", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Downtime_Employee_AssignToNumber",
                        column: x => x.AssignToNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Downtime_Issue_IssueId",
                        column: x => x.IssueId,
                        principalTable: "Issue",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Downtime_Employee_RequestNumber",
                        column: x => x.RequestNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Downtime_Results_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Results",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "HourByHour",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Hour = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    ResultId = table.Column<int>(nullable: false),
                    ResourceCode = table.Column<string>(nullable: false),
                    Meta = table.Column<int>(nullable: false),
                    Pieces = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_HourByHour", x => x.Id);
                    table.ForeignKey(
                        name: "FK_HourByHour_Warehouse_ResourceCode",
                        column: x => x.ResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_HourByHour_Results_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Results",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Labor",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    EmployeeNumber = table.Column<int>(nullable: false),
                    TimeStamp = table.Column<DateTime>(nullable: false),
                    TypeId = table.Column<int>(nullable: true),
                    ResultId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Labor", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Labor_Employee_EmployeeNumber",
                        column: x => x.EmployeeNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Labor_Results_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Results",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Labor_LaborType_TypeId",
                        column: x => x.TypeId,
                        principalTable: "LaborType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "ResultWorkOrder",
                columns: table => new
                {
                    ResultId = table.Column<int>(nullable: false),
                    WorkOrderId = table.Column<string>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ResultWorkOrder", x => new { x.ResultId, x.WorkOrderId });
                    table.ForeignKey(
                        name: "FK_ResultWorkOrder_Results_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Results",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ResultWorkOrder_WorkOrder_WorkOrderId",
                        column: x => x.WorkOrderId,
                        principalTable: "WorkOrder",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Contact",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PersonId = table.Column<int>(nullable: false),
                    JobTitle = table.Column<string>(maxLength: 100, nullable: true),
                    Department = table.Column<string>(maxLength: 45, nullable: true),
                    BusinessName = table.Column<string>(maxLength: 100, nullable: true),
                    Manager = table.Column<string>(maxLength: 100, nullable: true),
                    Notes = table.Column<string>(maxLength: 250, nullable: true),
                    CompanyId = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Contact", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Contact_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Mail",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Email = table.Column<string>(nullable: false),
                    ContactId = table.Column<int>(nullable: true),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Mail", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Mail_Contact_ContactId",
                        column: x => x.ContactId,
                        principalTable: "Contact",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Mail_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Phone",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PhoneNumber = table.Column<string>(maxLength: 13, nullable: false),
                    PhoneExtension = table.Column<string>(maxLength: 13, nullable: true),
                    Type = table.Column<int>(nullable: false),
                    ContactId = table.Column<int>(nullable: true),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Phone", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Phone_Contact_ContactId",
                        column: x => x.ContactId,
                        principalTable: "Contact",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Phone_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Company",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(maxLength: 45, nullable: false),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    BussinesName = table.Column<string>(maxLength: 150, nullable: true),
                    Web = table.Column<string>(nullable: true),
                    BussinesPhoneId = table.Column<int>(nullable: true),
                    PrivacyPolicy = table.Column<string>(nullable: true),
                    BussinessType = table.Column<string>(maxLength: 100, nullable: true),
                    Observations = table.Column<string>(maxLength: 250, nullable: true),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    DeleteDate = table.Column<DateTime>(nullable: false),
                    Delete = table.Column<bool>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Company", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Company_Phone_BussinesPhoneId",
                        column: x => x.BussinesPhoneId,
                        principalTable: "Phone",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Address_PersonId",
                table: "Address",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Area_FacilityId",
                table: "Area",
                column: "FacilityId");

            migrationBuilder.CreateIndex(
                name: "IX_Break_BreaksGroupId",
                table: "Break",
                column: "BreaksGroupId");

            migrationBuilder.CreateIndex(
                name: "IX_Break_TypeId",
                table: "Break",
                column: "TypeId");

            migrationBuilder.CreateIndex(
                name: "IX_breaksGroups_ShiftId",
                table: "breaksGroups",
                column: "ShiftId");

            migrationBuilder.CreateIndex(
                name: "IX_Company_BussinesPhoneId",
                table: "Company",
                column: "BussinesPhoneId");

            migrationBuilder.CreateIndex(
                name: "IX_Contact_CompanyId",
                table: "Contact",
                column: "CompanyId");

            migrationBuilder.CreateIndex(
                name: "IX_Contact_PersonId",
                table: "Contact",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_AssignToNumber",
                table: "Downtime",
                column: "AssignToNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_IssueId",
                table: "Downtime",
                column: "IssueId");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_RequestNumber",
                table: "Downtime",
                column: "RequestNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_ResultId",
                table: "Downtime",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_BusinessUnitId",
                table: "Employee",
                column: "BusinessUnitId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_ContractId",
                table: "Employee",
                column: "ContractId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_PersonId",
                table: "Employee",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_PositionId",
                table: "Employee",
                column: "PositionId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_ShiftId",
                table: "Employee",
                column: "ShiftId");

            migrationBuilder.CreateIndex(
                name: "IX_Facility_LocationId",
                table: "Facility",
                column: "LocationId");

            migrationBuilder.CreateIndex(
                name: "IX_HourByHour_ResourceCode",
                table: "HourByHour",
                column: "ResourceCode");

            migrationBuilder.CreateIndex(
                name: "IX_HourByHour_ResultId",
                table: "HourByHour",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_Item_CategoryId",
                table: "Item",
                column: "CategoryId");

            migrationBuilder.CreateIndex(
                name: "IX_JobPosition_AreaId",
                table: "JobPosition",
                column: "AreaId");

            migrationBuilder.CreateIndex(
                name: "IX_JobPosition_AutorityId",
                table: "JobPosition",
                column: "AutorityId");

            migrationBuilder.CreateIndex(
                name: "IX_JobPosition_DepartmentId",
                table: "JobPosition",
                column: "DepartmentId");

            migrationBuilder.CreateIndex(
                name: "IX_Labor_EmployeeNumber",
                table: "Labor",
                column: "EmployeeNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Labor_ResultId",
                table: "Labor",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_Labor_TypeId",
                table: "Labor",
                column: "TypeId");

            migrationBuilder.CreateIndex(
                name: "IX_License_PersonId",
                table: "License",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Location_AddressId",
                table: "Location",
                column: "AddressId");

            migrationBuilder.CreateIndex(
                name: "IX_Mail_ContactId",
                table: "Mail",
                column: "ContactId");

            migrationBuilder.CreateIndex(
                name: "IX_Mail_PersonId",
                table: "Mail",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_OperationTime_RoutId",
                table: "OperationTime",
                column: "RoutId");

            migrationBuilder.CreateIndex(
                name: "IX_OperationTime_WarehouseCode",
                table: "OperationTime",
                column: "WarehouseCode");

            migrationBuilder.CreateIndex(
                name: "IX_Person_BloodTypeGroup",
                table: "Person",
                column: "BloodTypeGroup");

            migrationBuilder.CreateIndex(
                name: "IX_Phone_ContactId",
                table: "Phone",
                column: "ContactId");

            migrationBuilder.CreateIndex(
                name: "IX_Phone_PersonId",
                table: "Phone",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Plannings_OperationTimeId",
                table: "Plannings",
                column: "OperationTimeId");

            migrationBuilder.CreateIndex(
                name: "IX_RefreshToken_UserId",
                table: "RefreshToken",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_Results_BreaksId",
                table: "Results",
                column: "BreaksId");

            migrationBuilder.CreateIndex(
                name: "IX_Results_ResourceCode",
                table: "Results",
                column: "ResourceCode");

            migrationBuilder.CreateIndex(
                name: "IX_Results_ShiftId",
                table: "Results",
                column: "ShiftId");

            migrationBuilder.CreateIndex(
                name: "IX_Results_SubResourceCode",
                table: "Results",
                column: "SubResourceCode");

            migrationBuilder.CreateIndex(
                name: "IX_Results_WorkOrderId",
                table: "Results",
                column: "WorkOrderId");

            migrationBuilder.CreateIndex(
                name: "IX_ResultWorkOrder_WorkOrderId",
                table: "ResultWorkOrder",
                column: "WorkOrderId");

            migrationBuilder.CreateIndex(
                name: "IX_Tracking_CloseEmployeeNumber",
                table: "Tracking",
                column: "CloseEmployeeNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Tracking_OperationTimeId",
                table: "Tracking",
                column: "OperationTimeId");

            migrationBuilder.CreateIndex(
                name: "IX_Tracking_RejectEmployeeNumber",
                table: "Tracking",
                column: "RejectEmployeeNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Tracking_ResourceCode",
                table: "Tracking",
                column: "ResourceCode");

            migrationBuilder.CreateIndex(
                name: "IX_Tracking_StartEmployeeNumber",
                table: "Tracking",
                column: "StartEmployeeNumber");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_FacilityId",
                table: "Warehouse",
                column: "FacilityId");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_GroupId",
                table: "Warehouse",
                column: "GroupId");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_TypeId",
                table: "Warehouse",
                column: "TypeId");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_UnitCode",
                table: "Warehouse",
                column: "UnitCode");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_AreaId",
                table: "Warehouse",
                column: "AreaId");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouse_BreakGroupId",
                table: "Warehouse",
                column: "BreakGroupId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkOrder_OperationTimeId",
                table: "WorkOrder",
                column: "OperationTimeId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkOrder_RoutId",
                table: "WorkOrder",
                column: "RoutId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkOrder_UMCode",
                table: "WorkOrder",
                column: "UMCode");

            migrationBuilder.AddForeignKey(
                name: "FK_Contact_Company_CompanyId",
                table: "Contact",
                column: "CompanyId",
                principalTable: "Company",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Contact_Person_PersonId",
                table: "Contact");

            migrationBuilder.DropForeignKey(
                name: "FK_Phone_Person_PersonId",
                table: "Phone");

            migrationBuilder.DropForeignKey(
                name: "FK_Company_Phone_BussinesPhoneId",
                table: "Company");

            migrationBuilder.DropTable(
                name: "Break");

            migrationBuilder.DropTable(
                name: "Downtime");

            migrationBuilder.DropTable(
                name: "HourByHour");

            migrationBuilder.DropTable(
                name: "Item");

            migrationBuilder.DropTable(
                name: "Labor");

            migrationBuilder.DropTable(
                name: "License");

            migrationBuilder.DropTable(
                name: "Mail");

            migrationBuilder.DropTable(
                name: "Partnership");

            migrationBuilder.DropTable(
                name: "Plannings");

            migrationBuilder.DropTable(
                name: "RefreshToken");

            migrationBuilder.DropTable(
                name: "ResultWorkOrder");

            migrationBuilder.DropTable(
                name: "Tracking");

            migrationBuilder.DropTable(
                name: "BreakType");

            migrationBuilder.DropTable(
                name: "Issue");

            migrationBuilder.DropTable(
                name: "ProductCategory");

            migrationBuilder.DropTable(
                name: "LaborType");

            migrationBuilder.DropTable(
                name: "User");

            migrationBuilder.DropTable(
                name: "Results");

            migrationBuilder.DropTable(
                name: "Employee");

            migrationBuilder.DropTable(
                name: "WorkOrder");

            migrationBuilder.DropTable(
                name: "BusinessUnit");

            migrationBuilder.DropTable(
                name: "Contract");

            migrationBuilder.DropTable(
                name: "JobPosition");

            migrationBuilder.DropTable(
                name: "OperationTime");

            migrationBuilder.DropTable(
                name: "Autority");

            migrationBuilder.DropTable(
                name: "Department");

            migrationBuilder.DropTable(
                name: "Rout");

            migrationBuilder.DropTable(
                name: "Warehouse");

            migrationBuilder.DropTable(
                name: "WarehouseGroup");

            migrationBuilder.DropTable(
                name: "WarehouseType");

            migrationBuilder.DropTable(
                name: "UM");

            migrationBuilder.DropTable(
                name: "Area");

            migrationBuilder.DropTable(
                name: "breaksGroups");

            migrationBuilder.DropTable(
                name: "Facility");

            migrationBuilder.DropTable(
                name: "Shift");

            migrationBuilder.DropTable(
                name: "Location");

            migrationBuilder.DropTable(
                name: "Address");

            migrationBuilder.DropTable(
                name: "Person");

            migrationBuilder.DropTable(
                name: "BloodType");

            migrationBuilder.DropTable(
                name: "Phone");

            migrationBuilder.DropTable(
                name: "Contact");

            migrationBuilder.DropTable(
                name: "Company");
        }
    }
}
