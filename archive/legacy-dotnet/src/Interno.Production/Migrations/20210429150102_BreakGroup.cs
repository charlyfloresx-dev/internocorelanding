using Microsoft.EntityFrameworkCore.Migrations;

namespace Interno.Production.Migrations
{
    public partial class BreakGroup : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Break_breaksGroups_BreaksGroupId",
                table: "Break");

            migrationBuilder.DropIndex(
                name: "IX_Break_BreaksGroupId",
                table: "Break");

            migrationBuilder.DropColumn(
                name: "BreaksGroupId",
                table: "Break");

            migrationBuilder.AddColumn<int>(
                name: "BreakGroupId",
                table: "Break",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.CreateIndex(
                name: "IX_Break_BreakGroupId",
                table: "Break",
                column: "BreakGroupId");

            migrationBuilder.AddForeignKey(
                name: "FK_Break_breaksGroups_BreakGroupId",
                table: "Break",
                column: "BreakGroupId",
                principalTable: "breaksGroups",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Break_breaksGroups_BreakGroupId",
                table: "Break");

            migrationBuilder.DropIndex(
                name: "IX_Break_BreakGroupId",
                table: "Break");

            migrationBuilder.DropColumn(
                name: "BreakGroupId",
                table: "Break");

            migrationBuilder.AddColumn<int>(
                name: "BreaksGroupId",
                table: "Break",
                type: "int",
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_Break_BreaksGroupId",
                table: "Break",
                column: "BreaksGroupId");

            migrationBuilder.AddForeignKey(
                name: "FK_Break_breaksGroups_BreaksGroupId",
                table: "Break",
                column: "BreaksGroupId",
                principalTable: "breaksGroups",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);
        }
    }
}
