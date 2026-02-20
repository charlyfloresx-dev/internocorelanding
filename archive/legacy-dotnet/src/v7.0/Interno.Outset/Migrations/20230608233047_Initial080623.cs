using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Interno.Outset.Migrations
{
    /// <inheritdoc />
    public partial class Initial080623 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterDatabase()
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BreakType",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BreakType", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Issue",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Type = table.Column<int>(type: "int", nullable: false),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Status = table.Column<bool>(type: "tinyint(1)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Issue", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Partnership",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(type: "varchar(15)", maxLength: 15, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Name = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Type = table.Column<int>(type: "int", nullable: false),
                    Status = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Partnership", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Shift",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(type: "varchar(13)", maxLength: 13, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Start = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    End = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    AvailableTime = table.Column<TimeSpan>(type: "time(6)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Shift", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "UM",
                columns: table => new
                {
                    Code = table.Column<string>(type: "varchar(4)", maxLength: 4, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Plural = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UM", x => x.Code);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "WarehouseGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WarehouseGroup", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "WarehouseType",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(25)", maxLength: 25, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Decription = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WarehouseType", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BreaksGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ShiftId = table.Column<int>(type: "int", nullable: false),
                    Name = table.Column<string>(type: "varchar(45)", maxLength: 45, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BreaksGroup", x => x.Id);
                    table.ForeignKey(
                        name: "FK_BreaksGroup_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Warehouse",
                columns: table => new
                {
                    Code = table.Column<string>(type: "varchar(13)", maxLength: 13, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Name = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    TypeId = table.Column<int>(type: "int", nullable: false),
                    Capacity = table.Column<float>(type: "float", nullable: false),
                    UnitCode = table.Column<string>(type: "varchar(4)", maxLength: 4, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    GroupId = table.Column<int>(type: "int", nullable: true),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    DeleteDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Delete = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Active = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Discriminator = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Warehouse", x => x.Code);
                    table.ForeignKey(
                        name: "FK_Warehouse_UM_UnitCode",
                        column: x => x.UnitCode,
                        principalTable: "UM",
                        principalColumn: "Code");
                    table.ForeignKey(
                        name: "FK_Warehouse_WarehouseGroup_GroupId",
                        column: x => x.GroupId,
                        principalTable: "WarehouseGroup",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Warehouse_WarehouseType_TypeId",
                        column: x => x.TypeId,
                        principalTable: "WarehouseType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Break",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Code = table.Column<string>(type: "varchar(15)", maxLength: 15, nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Start = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    End = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    TypeId = table.Column<int>(type: "int", nullable: true),
                    Duration = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    BreaksGroupId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Break", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Break_BreakType_TypeId",
                        column: x => x.TypeId,
                        principalTable: "BreakType",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Break_BreaksGroup_BreaksGroupId",
                        column: x => x.BreaksGroupId,
                        principalTable: "BreaksGroup",
                        principalColumn: "Id");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "OperationTime",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Guid = table.Column<Guid>(type: "char(36)", nullable: false, collation: "ascii_general_ci"),
                    Keying = table.Column<int>(type: "int", nullable: false),
                    Product = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    WarehouseCode = table.Column<string>(type: "varchar(13)", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Operation = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Operators = table.Column<int>(type: "int", nullable: false),
                    WorkControl = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    RunTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    SetTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    Hours = table.Column<double>(type: "double", nullable: false),
                    LMPU = table.Column<double>(type: "double", nullable: false),
                    Inprovement = table.Column<double>(type: "double", nullable: false),
                    OffSet = table.Column<decimal>(type: "decimal(65,30)", nullable: false),
                    Repeat = table.Column<int>(type: "int", nullable: false),
                    Cost = table.Column<decimal>(type: "decimal(65,30)", nullable: false),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Username = table.Column<string>(type: "varchar(100)", maxLength: 100, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_OperationTime", x => x.Id);
                    table.ForeignKey(
                        name: "FK_OperationTime_Warehouse_WarehouseCode",
                        column: x => x.WarehouseCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Result",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Priority = table.Column<int>(type: "int", nullable: false),
                    Date = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    ResourceCode = table.Column<string>(type: "varchar(13)", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    SubResourceCode = table.Column<string>(type: "varchar(13)", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    ShiftId = table.Column<int>(type: "int", nullable: false),
                    BreaksId = table.Column<int>(type: "int", nullable: true),
                    Operators = table.Column<int>(type: "int", nullable: false),
                    LeadTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    InitialTime = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    ScheduledStops = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    ProductiveTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    ScheduledOperatingTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    OperativeTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    OverTimeEnd = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    OverTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    PlanedTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    Item = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    WorkOrder = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    OrderQty = table.Column<int>(type: "int", nullable: false),
                    PlanQty = table.Column<int>(type: "int", nullable: false),
                    Actual = table.Column<int>(type: "int", nullable: false),
                    Rate = table.Column<double>(type: "double", nullable: false),
                    OEE = table.Column<double>(type: "double", nullable: false),
                    OE = table.Column<double>(type: "double", nullable: false),
                    TEP = table.Column<double>(type: "double", nullable: false),
                    Availability = table.Column<double>(type: "double", nullable: false),
                    Eficiency = table.Column<double>(type: "double", nullable: false),
                    FirstPassYield = table.Column<double>(type: "double", nullable: false),
                    OEE1 = table.Column<double>(type: "double", nullable: false),
                    TakTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    Capacity = table.Column<double>(type: "double", nullable: false),
                    LMPU = table.Column<double>(type: "double", nullable: false),
                    Inprovement = table.Column<double>(type: "double", nullable: false),
                    ShippingDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    WHSDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    SMKTDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Date1 = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Date2 = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    LeaderNumber = table.Column<int>(type: "int", nullable: false),
                    SupervisorNumber = table.Column<int>(type: "int", nullable: false),
                    Planner = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Result", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Result_BreaksGroup_BreaksId",
                        column: x => x.BreaksId,
                        principalTable: "BreaksGroup",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Result_Shift_ShiftId",
                        column: x => x.ShiftId,
                        principalTable: "Shift",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Result_Warehouse_ResourceCode",
                        column: x => x.ResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Result_Warehouse_SubResourceCode",
                        column: x => x.SubResourceCode,
                        principalTable: "Warehouse",
                        principalColumn: "Code");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "HourByHour",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Hour = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ResultId = table.Column<int>(type: "int", nullable: false),
                    ResourceCode = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Item = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    StdTime = table.Column<double>(type: "double", nullable: false),
                    Meta = table.Column<int>(type: "int", nullable: false),
                    Pieces = table.Column<int>(type: "int", nullable: false),
                    EmployeesQty = table.Column<int>(type: "int", nullable: false),
                    PaidHrs = table.Column<double>(type: "double", nullable: false),
                    Issues = table.Column<int>(type: "int", nullable: false),
                    Discriminator = table.Column<string>(type: "longtext", nullable: false)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_HourByHour", x => x.Id);
                    table.ForeignKey(
                        name: "FK_HourByHour_Result_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Result",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Labor",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    EmployeeNumber = table.Column<int>(type: "int", nullable: false),
                    ResourceCode = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Start = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    End = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    TypeId = table.Column<int>(type: "int", nullable: false),
                    ResultId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Labor", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Labor_Result_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Result",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Downtime",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Guid = table.Column<Guid>(type: "char(36)", nullable: false, collation: "ascii_general_ci"),
                    IssueId = table.Column<int>(type: "int", nullable: false),
                    ResultId = table.Column<int>(type: "int", nullable: false),
                    RequestNumber = table.Column<int>(type: "int", nullable: false),
                    Description = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Status = table.Column<int>(type: "int", nullable: false),
                    AssignToNumber = table.Column<int>(type: "int", nullable: false),
                    Action = table.Column<string>(type: "varchar(250)", maxLength: 250, nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CommitDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    ClosedDate = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Escalation = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Created = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Updated = table.Column<DateTime>(type: "datetime(6)", rowVersion: true, nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
                    HourByHourId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Downtime", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Downtime_HourByHour_HourByHourId",
                        column: x => x.HourByHourId,
                        principalTable: "HourByHour",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Downtime_Issue_IssueId",
                        column: x => x.IssueId,
                        principalTable: "Issue",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Downtime_Result_ResultId",
                        column: x => x.ResultId,
                        principalTable: "Result",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

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
                name: "IX_Downtime_HourByHourId",
                table: "Downtime",
                column: "HourByHourId");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_IssueId",
                table: "Downtime",
                column: "IssueId");

            migrationBuilder.CreateIndex(
                name: "IX_Downtime_ResultId",
                table: "Downtime",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_HourByHour_ResultId",
                table: "HourByHour",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_Labor_ResultId",
                table: "Labor",
                column: "ResultId");

            migrationBuilder.CreateIndex(
                name: "IX_OperationTime_WarehouseCode",
                table: "OperationTime",
                column: "WarehouseCode");

            migrationBuilder.CreateIndex(
                name: "IX_Result_BreaksId",
                table: "Result",
                column: "BreaksId");

            migrationBuilder.CreateIndex(
                name: "IX_Result_ResourceCode",
                table: "Result",
                column: "ResourceCode");

            migrationBuilder.CreateIndex(
                name: "IX_Result_ShiftId",
                table: "Result",
                column: "ShiftId");

            migrationBuilder.CreateIndex(
                name: "IX_Result_SubResourceCode",
                table: "Result",
                column: "SubResourceCode");

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
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Break");

            migrationBuilder.DropTable(
                name: "Downtime");

            migrationBuilder.DropTable(
                name: "Labor");

            migrationBuilder.DropTable(
                name: "OperationTime");

            migrationBuilder.DropTable(
                name: "Partnership");

            migrationBuilder.DropTable(
                name: "BreakType");

            migrationBuilder.DropTable(
                name: "HourByHour");

            migrationBuilder.DropTable(
                name: "Issue");

            migrationBuilder.DropTable(
                name: "Result");

            migrationBuilder.DropTable(
                name: "BreaksGroup");

            migrationBuilder.DropTable(
                name: "Warehouse");

            migrationBuilder.DropTable(
                name: "Shift");

            migrationBuilder.DropTable(
                name: "UM");

            migrationBuilder.DropTable(
                name: "WarehouseGroup");

            migrationBuilder.DropTable(
                name: "WarehouseType");
        }
    }
}
