using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

namespace Interno.Security.Migrations
{
    public partial class Initial : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Area",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Area", x => x.Id);
                });

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
                    Code = table.Column<string>(nullable: false),
                    Description = table.Column<string>(nullable: true),
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
                name: "Guardhouse",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(nullable: true),
                    Name = table.Column<string>(nullable: true),
                    Description = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Guardhouse", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Shift",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(nullable: true),
                    Start = table.Column<TimeSpan>(nullable: false),
                    End = table.Column<TimeSpan>(nullable: false),
                    Name = table.Column<string>(maxLength: 45, nullable: false),
                    Description = table.Column<string>(maxLength: 250, nullable: true),
                    AvailableTime = table.Column<TimeSpan>(nullable: false),
                    TotalTimeWorkday = table.Column<TimeSpan>(nullable: false),
                    TotalTimeBreaks = table.Column<TimeSpan>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Shift", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Persons",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LastNamePat = table.Column<string>(nullable: false),
                    LastNameMat = table.Column<string>(nullable: true),
                    FirstName = table.Column<string>(nullable: false),
                    MiddleName = table.Column<string>(nullable: true),
                    PrettyName = table.Column<string>(nullable: true),
                    SSN = table.Column<string>(nullable: true),
                    RFC = table.Column<string>(maxLength: 50, nullable: true),
                    CURP = table.Column<string>(maxLength: 50, nullable: true),
                    Birthday = table.Column<DateTime>(nullable: false),
                    Nationality = table.Column<string>(nullable: true),
                    Birthplace = table.Column<string>(nullable: true),
                    Gender = table.Column<int>(nullable: false),
                    Height = table.Column<float>(nullable: false),
                    Weight = table.Column<float>(nullable: false),
                    RelationshipStatus = table.Column<int>(nullable: false),
                    Childrens = table.Column<int>(nullable: false),
                    BloodTypeGroup = table.Column<string>(nullable: true),
                    Religion = table.Column<string>(nullable: true),
                    Passport = table.Column<bool>(nullable: false),
                    Visa = table.Column<bool>(nullable: false),
                    Sentry = table.Column<bool>(nullable: false),
                    GlobalEntry = table.Column<bool>(nullable: false),
                    TravelAvailability = table.Column<bool>(nullable: false),
                    Relocation = table.Column<bool>(nullable: false),
                    AboutMe = table.Column<string>(nullable: true),
                    Created = table.Column<DateTime>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    Suspended = table.Column<bool>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Persons", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Persons_BloodType_BloodTypeGroup",
                        column: x => x.BloodTypeGroup,
                        principalTable: "BloodType",
                        principalColumn: "Group",
                        onDelete: ReferentialAction.Restrict);
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
                name: "BreaksGroup",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(nullable: false),
                    Description = table.Column<string>(nullable: true),
                    ShiftId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BreaksGroup", x => x.Id);
                    table.ForeignKey(
                        name: "FK_BreaksGroup_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
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
                        name: "FK_Address_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Contact",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PersonId = table.Column<int>(nullable: false),
                    JobTitle = table.Column<string>(nullable: true),
                    Department = table.Column<string>(nullable: true),
                    BusinessName = table.Column<string>(nullable: true),
                    Manager = table.Column<string>(nullable: true),
                    Notes = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Contact", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Contact_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "License",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LicenseName = table.Column<string>(nullable: false),
                    Type = table.Column<string>(nullable: false),
                    Number = table.Column<string>(nullable: true),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_License", x => x.Id);
                    table.ForeignKey(
                        name: "FK_License_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Mail",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Email = table.Column<string>(nullable: false),
                    PersonId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Mail", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Mail_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "SecurityGuard",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PersonId = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SecurityGuard", x => x.Id);
                    table.ForeignKey(
                        name: "FK_SecurityGuard_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
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
                        name: "FK_Employee_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
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
                        name: "FK_Break_BreaksGroup_BreaksGroupId",
                        column: x => x.BreaksGroupId,
                        principalTable: "BreaksGroup",
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
                name: "Phone",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PhoneNumber = table.Column<string>(nullable: false),
                    PhoneExtension = table.Column<string>(nullable: true),
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
                        name: "FK_Phone_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "EmployeeLog",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    GuardhouseId = table.Column<int>(nullable: false),
                    Time = table.Column<DateTime>(nullable: false),
                    Type = table.Column<bool>(nullable: false),
                    SecurityGuardId = table.Column<int>(nullable: false),
                    EmployeeNumber = table.Column<int>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmployeeLog", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EmployeeLog_Employee_EmployeeNumber",
                        column: x => x.EmployeeNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_EmployeeLog_Guardhouse_GuardhouseId",
                        column: x => x.GuardhouseId,
                        principalTable: "Guardhouse",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_EmployeeLog_SecurityGuard_SecurityGuardId",
                        column: x => x.SecurityGuardId,
                        principalTable: "SecurityGuard",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "VisitLog",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    GuardhouseId = table.Column<int>(nullable: false),
                    Time = table.Column<DateTime>(nullable: false),
                    Type = table.Column<bool>(nullable: false),
                    SecurityGuardId = table.Column<int>(nullable: false),
                    PersonId = table.Column<int>(nullable: false),
                    VisitingNumber = table.Column<int>(nullable: false),
                    Subjet = table.Column<string>(nullable: false),
                    Badges = table.Column<int>(nullable: false),
                    IdentifyType = table.Column<int>(nullable: false),
                    Identification = table.Column<string>(nullable: false),
                    VehicleType = table.Column<int>(nullable: false),
                    VehicleRegistration = table.Column<string>(nullable: true),
                    Comment = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_VisitLog", x => x.Id);
                    table.ForeignKey(
                        name: "FK_VisitLog_Guardhouse_GuardhouseId",
                        column: x => x.GuardhouseId,
                        principalTable: "Guardhouse",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_VisitLog_Persons_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Persons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_VisitLog_SecurityGuard_SecurityGuardId",
                        column: x => x.SecurityGuardId,
                        principalTable: "SecurityGuard",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_VisitLog_Employee_VisitingNumber",
                        column: x => x.VisitingNumber,
                        principalTable: "Employee",
                        principalColumn: "Number",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Address_PersonId",
                table: "Address",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Break_BreaksGroupId",
                table: "Break",
                column: "BreaksGroupId");

            migrationBuilder.CreateIndex(
                name: "IX_Break_TypeId",
                table: "Break",
                column: "TypeId");

            migrationBuilder.CreateIndex(
                name: "IX_BreaksGroup_ShiftId",
                table: "BreaksGroup",
                column: "ShiftId");

            migrationBuilder.CreateIndex(
                name: "IX_Contact_PersonId",
                table: "Contact",
                column: "PersonId");

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
                name: "IX_EmployeeLog_EmployeeNumber",
                table: "EmployeeLog",
                column: "EmployeeNumber");

            migrationBuilder.CreateIndex(
                name: "IX_EmployeeLog_GuardhouseId",
                table: "EmployeeLog",
                column: "GuardhouseId");

            migrationBuilder.CreateIndex(
                name: "IX_EmployeeLog_SecurityGuardId",
                table: "EmployeeLog",
                column: "SecurityGuardId");

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
                name: "IX_License_PersonId",
                table: "License",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Mail_PersonId",
                table: "Mail",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Persons_BloodTypeGroup",
                table: "Persons",
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
                name: "IX_SecurityGuard_PersonId",
                table: "SecurityGuard",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_VisitLog_GuardhouseId",
                table: "VisitLog",
                column: "GuardhouseId");

            migrationBuilder.CreateIndex(
                name: "IX_VisitLog_PersonId",
                table: "VisitLog",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_VisitLog_SecurityGuardId",
                table: "VisitLog",
                column: "SecurityGuardId");

            migrationBuilder.CreateIndex(
                name: "IX_VisitLog_VisitingNumber",
                table: "VisitLog",
                column: "VisitingNumber");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Address");

            migrationBuilder.DropTable(
                name: "Break");

            migrationBuilder.DropTable(
                name: "EmployeeLog");

            migrationBuilder.DropTable(
                name: "License");

            migrationBuilder.DropTable(
                name: "Mail");

            migrationBuilder.DropTable(
                name: "Phone");

            migrationBuilder.DropTable(
                name: "VisitLog");

            migrationBuilder.DropTable(
                name: "BreaksGroup");

            migrationBuilder.DropTable(
                name: "BreakType");

            migrationBuilder.DropTable(
                name: "Contact");

            migrationBuilder.DropTable(
                name: "Guardhouse");

            migrationBuilder.DropTable(
                name: "SecurityGuard");

            migrationBuilder.DropTable(
                name: "Employee");

            migrationBuilder.DropTable(
                name: "BusinessUnit");

            migrationBuilder.DropTable(
                name: "Contract");

            migrationBuilder.DropTable(
                name: "Persons");

            migrationBuilder.DropTable(
                name: "JobPosition");

            migrationBuilder.DropTable(
                name: "Shift");

            migrationBuilder.DropTable(
                name: "BloodType");

            migrationBuilder.DropTable(
                name: "Area");

            migrationBuilder.DropTable(
                name: "Autority");

            migrationBuilder.DropTable(
                name: "Department");
        }
    }
}
