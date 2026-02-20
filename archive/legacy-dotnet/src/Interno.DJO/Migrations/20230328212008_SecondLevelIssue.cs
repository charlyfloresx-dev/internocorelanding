using Microsoft.EntityFrameworkCore.Migrations;

namespace Interno.DJO.Migrations
{
    public partial class SecondLevelIssue : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Downtimes_Issues_IssueId",
                table: "Downtimes");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Issues",
                table: "Issues");

            migrationBuilder.RenameTable(
                name: "Issues",
                newName: "Issue");

            migrationBuilder.AddColumn<string>(
                name: "Discriminator",
                table: "Issue",
                nullable: false);

            migrationBuilder.AddColumn<int>(
                name: "Flag",
                table: "Issue",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "Level1",
                table: "Issue",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Level2",
                table: "Issue",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "PIC",
                table: "Issue",
                nullable: true);

            migrationBuilder.AddPrimaryKey(
                name: "PK_Issue",
                table: "Issue",
                column: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Downtimes_Issue_IssueId",
                table: "Downtimes",
                column: "IssueId",
                principalTable: "Issue",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Downtimes_Issue_IssueId",
                table: "Downtimes");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Issue",
                table: "Issue");

            migrationBuilder.DropColumn(
                name: "Discriminator",
                table: "Issue");

            migrationBuilder.DropColumn(
                name: "Flag",
                table: "Issue");

            migrationBuilder.DropColumn(
                name: "Level1",
                table: "Issue");

            migrationBuilder.DropColumn(
                name: "Level2",
                table: "Issue");

            migrationBuilder.DropColumn(
                name: "PIC",
                table: "Issue");

            migrationBuilder.RenameTable(
                name: "Issue",
                newName: "Issues");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Issues",
                table: "Issues",
                column: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Downtimes_Issues_IssueId",
                table: "Downtimes",
                column: "IssueId",
                principalTable: "Issues",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
