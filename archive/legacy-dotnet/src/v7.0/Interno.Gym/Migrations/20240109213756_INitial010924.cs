using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Interno.Gym.Migrations
{
    /// <inheritdoc />
    public partial class INitial010924 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterDatabase()
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BloodType",
                columns: table => new
                {
                    Group = table.Column<string>(type: "varchar(3)", maxLength: 3, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Donate = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Receive = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BloodType", x => x.Group);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Lessons",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Room = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Lessons", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Subscriptions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "char(36)", nullable: false, collation: "ascii_general_ci"),
                    PartnerId = table.Column<int>(type: "int", nullable: false),
                    Type = table.Column<int>(type: "int", nullable: false),
                    Start = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    End = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Coupon = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    CouponNumber = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Active = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Subscriptions", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Address",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Type = table.Column<int>(type: "int", nullable: false),
                    AddressLine1 = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    AddressLine2 = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    City = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    ZipCode = table.Column<int>(type: "int", nullable: false),
                    State = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Country = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Region = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    PersonId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Address", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Company",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    BussinesName = table.Column<string>(type: "varchar(150)", maxLength: 150, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Web = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    BussinesPhoneId = table.Column<int>(type: "int", nullable: true),
                    PrivacyPolicy = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    BussinessType = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Observations = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    DeleteDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Delete = table.Column<bool>(type: "tinyint(1)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Company", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Location",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    AddressId = table.Column<int>(type: "int", nullable: true),
                    CompanyId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Location", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Location_Address_AddressId",
                        column: x => x.AddressId,
                        principalTable: "Address",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Location_Company_CompanyId",
                        column: x => x.CompanyId,
                        principalTable: "Company",
                        principalColumn: "Id");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Contact",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PersonId = table.Column<int>(type: "int", nullable: false),
                    JobTitle = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Department = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    BusinessName = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Manager = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Notes = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CompanyId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Contact", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Contact_Company_CompanyId",
                        column: x => x.CompanyId,
                        principalTable: "Company",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "License",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LicenseName = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Type = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Number = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    PersonId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_License", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Mail",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Email = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    ContactId = table.Column<int>(type: "int", nullable: true),
                    PersonId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Mail", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Mail_Contact_ContactId",
                        column: x => x.ContactId,
                        principalTable: "Contact",
                        principalColumn: "Id");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Person",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LastNamePat = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    LastNameMat = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    FirstName = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    MiddleName = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    PrettyName = table.Column<string>(type: "varchar(150)", maxLength: 150, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    SSN = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    RFC = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CURP = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Birthday = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Nationality = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Birthplace = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Gender = table.Column<int>(type: "int", nullable: false),
                    Height = table.Column<float>(type: "float", nullable: false),
                    Weight = table.Column<float>(type: "float", nullable: false),
                    RelationshipStatus = table.Column<int>(type: "int", nullable: false),
                    Childrens = table.Column<int>(type: "int", nullable: false),
                    BloodTypeGroup = table.Column<string>(type: "varchar(3)", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Religion = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Passport = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Visa = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Sentry = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    GlobalEntry = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    TravelAvailability = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Relocation = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    AboutMe = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Created = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    Suspended = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Discriminator = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    ScheduledLessonId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Person", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Person_BloodType_BloodTypeGroup",
                        column: x => x.BloodTypeGroup,
                        principalTable: "BloodType",
                        principalColumn: "Group");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Phone",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PhoneNumber = table.Column<string>(type: "varchar(13)", maxLength: 13, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    PhoneExtension = table.Column<string>(type: "varchar(13)", maxLength: 13, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Type = table.Column<int>(type: "int", nullable: false),
                    ContactId = table.Column<int>(type: "int", nullable: true),
                    PersonId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Phone", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Phone_Contact_ContactId",
                        column: x => x.ContactId,
                        principalTable: "Contact",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Phone_Person_PersonId",
                        column: x => x.PersonId,
                        principalTable: "Person",
                        principalColumn: "Id");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ScheduledLessons",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    LessonId = table.Column<int>(type: "int", nullable: false),
                    TutorId = table.Column<int>(type: "int", nullable: false),
                    Location = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Start = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    End = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScheduledLessons", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ScheduledLessons_Lessons_LessonId",
                        column: x => x.LessonId,
                        principalTable: "Lessons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ScheduledLessons_Person_TutorId",
                        column: x => x.TutorId,
                        principalTable: "Person",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateIndex(
                name: "IX_Address_PersonId",
                table: "Address",
                column: "PersonId");

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
                name: "IX_License_PersonId",
                table: "License",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Location_AddressId",
                table: "Location",
                column: "AddressId");

            migrationBuilder.CreateIndex(
                name: "IX_Location_CompanyId",
                table: "Location",
                column: "CompanyId");

            migrationBuilder.CreateIndex(
                name: "IX_Mail_ContactId",
                table: "Mail",
                column: "ContactId");

            migrationBuilder.CreateIndex(
                name: "IX_Mail_PersonId",
                table: "Mail",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_Person_BloodTypeGroup",
                table: "Person",
                column: "BloodTypeGroup");

            migrationBuilder.CreateIndex(
                name: "IX_Person_ScheduledLessonId",
                table: "Person",
                column: "ScheduledLessonId");

            migrationBuilder.CreateIndex(
                name: "IX_Phone_ContactId",
                table: "Phone",
                column: "ContactId");

            migrationBuilder.CreateIndex(
                name: "IX_Phone_PersonId",
                table: "Phone",
                column: "PersonId");

            migrationBuilder.CreateIndex(
                name: "IX_ScheduledLessons_LessonId",
                table: "ScheduledLessons",
                column: "LessonId");

            migrationBuilder.CreateIndex(
                name: "IX_ScheduledLessons_TutorId",
                table: "ScheduledLessons",
                column: "TutorId");

            migrationBuilder.AddForeignKey(
                name: "FK_Address_Person_PersonId",
                table: "Address",
                column: "PersonId",
                principalTable: "Person",
                principalColumn: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Company_Phone_BussinesPhoneId",
                table: "Company",
                column: "BussinesPhoneId",
                principalTable: "Phone",
                principalColumn: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Contact_Person_PersonId",
                table: "Contact",
                column: "PersonId",
                principalTable: "Person",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_License_Person_PersonId",
                table: "License",
                column: "PersonId",
                principalTable: "Person",
                principalColumn: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Mail_Person_PersonId",
                table: "Mail",
                column: "PersonId",
                principalTable: "Person",
                principalColumn: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Person_ScheduledLessons_ScheduledLessonId",
                table: "Person",
                column: "ScheduledLessonId",
                principalTable: "ScheduledLessons",
                principalColumn: "Id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Contact_Person_PersonId",
                table: "Contact");

            migrationBuilder.DropForeignKey(
                name: "FK_Phone_Person_PersonId",
                table: "Phone");

            migrationBuilder.DropForeignKey(
                name: "FK_ScheduledLessons_Person_TutorId",
                table: "ScheduledLessons");

            migrationBuilder.DropForeignKey(
                name: "FK_Company_Phone_BussinesPhoneId",
                table: "Company");

            migrationBuilder.DropTable(
                name: "License");

            migrationBuilder.DropTable(
                name: "Location");

            migrationBuilder.DropTable(
                name: "Mail");

            migrationBuilder.DropTable(
                name: "Subscriptions");

            migrationBuilder.DropTable(
                name: "Address");

            migrationBuilder.DropTable(
                name: "Person");

            migrationBuilder.DropTable(
                name: "BloodType");

            migrationBuilder.DropTable(
                name: "ScheduledLessons");

            migrationBuilder.DropTable(
                name: "Lessons");

            migrationBuilder.DropTable(
                name: "Phone");

            migrationBuilder.DropTable(
                name: "Contact");

            migrationBuilder.DropTable(
                name: "Company");
        }
    }
}
