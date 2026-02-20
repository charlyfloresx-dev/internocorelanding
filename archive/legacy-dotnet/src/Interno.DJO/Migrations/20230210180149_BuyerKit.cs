using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

namespace Interno.DJO.Migrations
{
    public partial class BuyerKit : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // migrationBuilder.CreateTable(
            //     name: "BackOrders",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Date = table.Column<DateTime>(nullable: false),
            //         Item = table.Column<string>(nullable: true),
            //         Quantity = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Amount = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         BOMAffectedAmount = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BackOrders", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "BalanceOnHands",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Customer = table.Column<string>(nullable: true),
            //         ReceiveingId = table.Column<int>(nullable: false),
            //         ControlNumber = table.Column<int>(nullable: false),
            //         PartNumber = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         ReceivedDate = table.Column<DateTime>(nullable: false),
            //         Qty = table.Column<int>(nullable: false),
            //         Unit = table.Column<string>(nullable: true),
            //         Bal = table.Column<int>(nullable: false),
            //         DaysIn = table.Column<int>(nullable: false),
            //         Location = table.Column<string>(nullable: true),
            //         Weight = table.Column<int>(nullable: false),
            //         Shipper = table.Column<string>(nullable: true),
            //         PO = table.Column<string>(nullable: true),
            //         Carrier = table.Column<string>(nullable: true),
            //         FB = table.Column<string>(nullable: true),
            //         Inbond = table.Column<int>(nullable: false),
            //         InbondIssueDate = table.Column<DateTime>(nullable: false),
            //         Comments = table.Column<string>(nullable: true),
            //         Reference = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BalanceOnHands", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Bins",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(maxLength: 50, nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Item = table.Column<string>(maxLength: 50, nullable: true),
            //         Resource = table.Column<string>(maxLength: 50, nullable: true),
            //         SubResource = table.Column<string>(maxLength: 50, nullable: true),
            //         Location = table.Column<string>(maxLength: 50, nullable: true),
            //         Qty = table.Column<int>(nullable: false),
            //         Logo = table.Column<string>(maxLength: 50, nullable: true),
            //         Hours = table.Column<int>(nullable: false),
            //         UOM = table.Column<string>(maxLength: 5, nullable: true),
            //         PackingType = table.Column<string>(maxLength: 50, nullable: true),
            //         BinSize = table.Column<string>(maxLength: 50, nullable: true),
            //         QtyBines = table.Column<int>(nullable: false),
            //         Color = table.Column<string>(maxLength: 50, nullable: true),
            //         SubInvetorySource = table.Column<string>(maxLength: 50, nullable: true),
            //         LocatorSource = table.Column<string>(maxLength: 50, nullable: true),
            //         Bloqued = table.Column<bool>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Bins", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "BlankPOs",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         FOB = table.Column<string>(nullable: true),
            //         Terms = table.Column<string>(nullable: true),
            //         AgreedUnitPrice = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         BuyerName = table.Column<string>(nullable: true),
            //         CurrencyCode = table.Column<string>(nullable: true),
            //         ItemDescription = table.Column<string>(nullable: true),
            //         Line = table.Column<int>(nullable: false),
            //         PO = table.Column<int>(nullable: false),
            //         TypePO = table.Column<string>(nullable: true),
            //         QtyOutstanding = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         AmountOutstanding = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ReleaseAuthStatus = table.Column<string>(nullable: true),
            //         ReleaseCloseCode = table.Column<string>(nullable: true),
            //         ReleaseNumber = table.Column<int>(nullable: false),
            //         ShipToOrg = table.Column<string>(nullable: true),
            //         ShipmentType = table.Column<string>(nullable: true),
            //         Vendor = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         NeedByDate = table.Column<DateTime>(nullable: false),
            //         POCreationDate = table.Column<DateTime>(nullable: false),
            //         CreationDate = table.Column<DateTime>(nullable: false),
            //         PromisedDate = table.Column<DateTime>(nullable: false),
            //         ReleaseDate = table.Column<DateTime>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BlankPOs", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "BOMs",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         TypeDescription = table.Column<string>(nullable: true),
            //         Module = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         Level = table.Column<int>(nullable: false),
            //         Parent = table.Column<string>(nullable: true),
            //         Component = table.Column<string>(nullable: true),
            //         ComponentDescription = table.Column<string>(nullable: true),
            //         ComponenQuantityPer = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         UOM = table.Column<string>(nullable: true),
            //         ComponentType = table.Column<string>(nullable: true),
            //         ComponentModule = table.Column<string>(nullable: true),
            //         ComponentSupplierType = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BOMs", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "BreakType",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Name = table.Column<string>(maxLength: 45, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BreakType", x => x.Id);
            //     });

            migrationBuilder.CreateTable(
                name: "BuyerKits",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Date = table.Column<DateTime>(nullable: false),
                    Item = table.Column<string>(nullable: true),
                    Site = table.Column<string>(nullable: true),
                    SRC = table.Column<string>(nullable: true),
                    Type = table.Column<string>(nullable: true),
                    Status = table.Column<string>(nullable: true),
                    ABC = table.Column<string>(nullable: true),
                    Buyer = table.Column<string>(nullable: true),
                    ItemDescription = table.Column<string>(nullable: true),
                    FirstShortage = table.Column<DateTime>(nullable: false),
                    DOS = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    SS = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    UOM = table.Column<string>(nullable: true),
                    LT = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    Min = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    Max = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    Multi = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    Supplier = table.Column<string>(nullable: true),
                    OH = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    PO = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    PLO = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
                    DMD = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BuyerKits", x => x.Id);
                });

            // migrationBuilder.CreateTable(
            //     name: "Completions",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         TransDateTime = table.Column<DateTime>(nullable: false),
            //         JobNumber = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         ItemType = table.Column<string>(nullable: true),
            //         Qty = table.Column<decimal>(nullable: false),
            //         Module = table.Column<string>(nullable: true),
            //         ModuleDesc = table.Column<string>(nullable: true),
            //         ProductBrand = table.Column<string>(nullable: true),
            //         ValueStream = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Completions", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "DJOLogTypes",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Value = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_DJOLogTypes", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Goals",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         ResourceCode = table.Column<string>(nullable: false),
            //         Hour = table.Column<TimeSpan>(nullable: false),
            //         Qty = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Goals", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "IncomingPriorities",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Priority = table.Column<int>(nullable: false),
            //         Item = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         Reference = table.Column<string>(nullable: true),
            //         ETA = table.Column<DateTime>(nullable: false),
            //         ModuleAffec = table.Column<string>(nullable: true),
            //         ProdInpac = table.Column<DateTime>(nullable: false),
            //         Routing = table.Column<string>(nullable: true),
            //         Comment = table.Column<string>(nullable: true),
            //         Available = table.Column<bool>(nullable: false),
            //         AvailableDate = table.Column<DateTime>(nullable: true),
            //         CreatedUser = table.Column<string>(nullable: true),
            //         UpdatedUser = table.Column<string>(nullable: true),
            //         Created = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Updated = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_IncomingPriorities", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Issues",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Type = table.Column<int>(nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: false),
            //         Status = table.Column<bool>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Issues", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "ItemPrices",
            //     columns: table => new
            //     {
            //         Item = table.Column<string>(nullable: false),
            //         Site = table.Column<string>(nullable: false),
            //         Description = table.Column<string>(nullable: true),
            //         UOM = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         CorporateBrand = table.Column<string>(nullable: true),
            //         ABC = table.Column<string>(nullable: false),
            //         StdCost = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Buyer = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         MOQ = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         MPQ = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         LeadTime = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         PriorityCode = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         SafetyStock = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_ItemPrices", x => new { x.Item, x.Site });
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Machines",
            //     columns: table => new
            //     {
            //         Id = table.Column<string>(nullable: false),
            //         Module = table.Column<string>(nullable: true),
            //         BussinesUnit = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Machines", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "MoveOrders",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Number = table.Column<long>(nullable: false),
            //         Description = table.Column<string>(nullable: true),
            //         CreatedDateTime = table.Column<DateTime>(nullable: false),
            //         Type = table.Column<string>(nullable: true),
            //         Line = table.Column<int>(nullable: false),
            //         TransactionType = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         Rev = table.Column<string>(nullable: true),
            //         SourceSubinv = table.Column<string>(nullable: true),
            //         SourceLocator = table.Column<string>(nullable: true),
            //         DestinationSubinv = table.Column<string>(nullable: true),
            //         DestinationLocator = table.Column<string>(nullable: true),
            //         DestinationAcoount = table.Column<string>(nullable: true),
            //         LotNumber = table.Column<string>(nullable: true),
            //         ExpirationDate = table.Column<DateTime>(nullable: false),
            //         SerialFrom = table.Column<string>(nullable: true),
            //         SerialTo = table.Column<string>(nullable: true),
            //         UnitNumber = table.Column<string>(nullable: true),
            //         UOM = table.Column<string>(nullable: true),
            //         TransactionQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         RequestedQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         TransactionDate = table.Column<DateTime>(nullable: false),
            //         OnTimeMetric = table.Column<bool>(nullable: false),
            //         RequiredQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         DeliveredQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         AllocatedQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         RemainingQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         SecondaryUOM = table.Column<string>(nullable: true),
            //         SecondaryQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         SecondaryRequestedQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         SecondatyRequiredQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         SecondaryDeliveredQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         SecondaryAllocatedQty = table.Column<decimal>(type: "decimal(16,2)", nullable: false),
            //         Grade = table.Column<string>(nullable: true),
            //         DateRequired = table.Column<DateTime>(nullable: false),
            //         Reason = table.Column<string>(nullable: true),
            //         Reference = table.Column<string>(nullable: true),
            //         Route = table.Column<string>(nullable: true),
            //         Cell = table.Column<string>(nullable: true),
            //         Priority = table.Column<string>(nullable: true),
            //         LineStatus = table.Column<string>(nullable: true),
            //         StatusDate = table.Column<DateTime>(nullable: false),
            //         CreatedBy = table.Column<string>(nullable: true),
            //         PriorityLevel = table.Column<int>(nullable: false),
            //         AssortmenStart = table.Column<DateTime>(nullable: false),
            //         AssortmentUser = table.Column<int>(nullable: false),
            //         Status = table.Column<int>(nullable: false),
            //         Updated = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_MoveOrders", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "OpenSummaryReports",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Site = table.Column<string>(nullable: true),
            //         Part = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Organization = table.Column<string>(nullable: true),
            //         Order = table.Column<string>(nullable: true),
            //         Line = table.Column<string>(nullable: true),
            //         OrderType = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         SupplierDescription = table.Column<string>(nullable: true),
            //         UOM = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         OrgQuantity = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         OpenQuantity = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ShipTo = table.Column<string>(nullable: true),
            //         DueDate = table.Column<DateTime>(nullable: false),
            //         OriginalDueDate = table.Column<DateTime>(nullable: false),
            //         UnitPrice = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Amount = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         FirstShortageDate = table.Column<DateTime>(nullable: true),
            //         RecomendedDate = table.Column<DateTime>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_OpenSummaryReports", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "OTDReceipts",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         OrganizationCode = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         Vendor = table.Column<string>(nullable: true),
            //         PO = table.Column<int>(nullable: false),
            //         Line = table.Column<int>(nullable: false),
            //         Release = table.Column<int>(nullable: false),
            //         POshipmentNumber = table.Column<int>(nullable: false),
            //         ReceiptCreationDate = table.Column<DateTime>(nullable: false),
            //         QuantityReceived = table.Column<decimal>(nullable: false),
            //         Buyer = table.Column<string>(nullable: true),
            //         PrimaryQuantity = table.Column<decimal>(nullable: false),
            //         PromisedDate = table.Column<DateTime>(nullable: false),
            //         TransactionType = table.Column<string>(nullable: true),
            //         TransactionType2 = table.Column<string>(nullable: true),
            //         OnTime = table.Column<bool>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_OTDReceipts", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Partnership",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Code = table.Column<string>(maxLength: 15, nullable: false),
            //         Name = table.Column<string>(maxLength: 250, nullable: false),
            //         Type = table.Column<int>(nullable: false),
            //         Status = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Partnership", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "PlannedPOs",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Site = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         StdCost = table.Column<decimal>(nullable: false),
            //         SupplyType = table.Column<string>(nullable: true),
            //         Line = table.Column<int>(nullable: false),
            //         EffQty = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         LeadTime = table.Column<int>(nullable: false),
            //         DaysToAcc = table.Column<int>(nullable: false),
            //         Action = table.Column<string>(nullable: true),
            //         StartDate = table.Column<DateTime>(nullable: false),
            //         DueDate = table.Column<DateTime>(nullable: false),
            //         Category = table.Column<string>(nullable: true),
            //         StdCostExt = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         PPV = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Spend = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_PlannedPOs", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "PurchaseOrders",
            //     columns: table => new
            //     {
            //         PO = table.Column<int>(nullable: false),
            //         Rel = table.Column<int>(nullable: false),
            //         Line = table.Column<int>(nullable: false),
            //         Ship = table.Column<int>(nullable: false),
            //         ShipTo = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         SupItem = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         QtyOrd = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         QtyRec = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         QtyBilled = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         QtyDue = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         QtyCancelled = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Promised = table.Column<DateTime>(nullable: true),
            //         NeedBy = table.Column<DateTime>(nullable: false),
            //         OrderDate = table.Column<DateTime>(nullable: false),
            //         Buyer = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         AuthorizationStatus = table.Column<string>(nullable: true),
            //         Price = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ShpAmount = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         UOM = table.Column<string>(nullable: true),
            //         Site = table.Column<string>(nullable: true),
            //         Curr = table.Column<string>(nullable: true),
            //         CountryOfOrigen = table.Column<string>(nullable: true),
            //         ReceiptRouting = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_PurchaseOrders", x => new { x.PO, x.Line, x.Rel, x.Ship });
            //     });

            // migrationBuilder.CreateTable(
            //     name: "PurchaseReceipts",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         PO = table.Column<int>(nullable: false),
            //         Line = table.Column<int>(nullable: false),
            //         POQty = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ReceivedDate = table.Column<DateTime>(nullable: false),
            //         ReceivedQty = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Product = table.Column<string>(nullable: true),
            //         SupplierName = table.Column<string>(nullable: true),
            //         VendorType = table.Column<string>(nullable: true),
            //         ProductName = table.Column<string>(nullable: true),
            //         ProductType = table.Column<string>(nullable: true),
            //         Site = table.Column<string>(nullable: true),
            //         POCreationDate = table.Column<DateTime>(nullable: false),
            //         POReleaseDate = table.Column<DateTime>(nullable: false),
            //         PromisedDate = table.Column<DateTime>(nullable: false),
            //         Buyer = table.Column<string>(nullable: true),
            //         FiscalYear = table.Column<int>(nullable: false),
            //         FiscalQuarter = table.Column<string>(nullable: true),
            //         FiscalPeriod = table.Column<string>(nullable: true),
            //         FiscalWeek = table.Column<string>(nullable: true),
            //         ReceiptAmount = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ReceivedPrice = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Category = table.Column<string>(nullable: true),
            //         StdCost = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         StdCostExt = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         PPV = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Spend = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_PurchaseReceipts", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Quotations",
            //     columns: table => new
            //     {
            //         Quote = table.Column<int>(nullable: false),
            //         Line = table.Column<int>(nullable: false),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Creation = table.Column<DateTime>(nullable: false),
            //         SupplierItem = table.Column<string>(nullable: true),
            //         Vendor = table.Column<string>(nullable: true),
            //         VendorSite = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: false),
            //         LastUpdate = table.Column<DateTime>(nullable: false),
            //         ShipTo = table.Column<string>(nullable: true),
            //         EefTo = table.Column<string>(nullable: true),
            //         EefFrom = table.Column<string>(nullable: true),
            //         BillTo = table.Column<string>(nullable: true),
            //         Term = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         UOM = table.Column<string>(nullable: true),
            //         UnitPrice = table.Column<decimal>(type: "decimal(16,4)", nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Quotations", x => new { x.Quote, x.Line });
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Rout",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Guid = table.Column<Guid>(nullable: false),
            //         Code = table.Column<string>(maxLength: 13, nullable: true),
            //         Name = table.Column<string>(maxLength: 100, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true),
            //         Revision = table.Column<string>(maxLength: 5, nullable: false),
            //         Target = table.Column<string>(maxLength: 25, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Rout", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "ScoreCards",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Partnership = table.Column<string>(nullable: true),
            //         Category = table.Column<string>(nullable: true),
            //         KPI = table.Column<string>(nullable: true),
            //         Frecuency = table.Column<int>(nullable: false),
            //         Target = table.Column<int>(nullable: false),
            //         FullScore = table.Column<decimal>(nullable: false),
            //         CalculationMethod = table.Column<string>(nullable: true),
            //         DataSource = table.Column<string>(nullable: true),
            //         Link = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_ScoreCards", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Shift",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Code = table.Column<string>(maxLength: 13, nullable: false),
            //         Start = table.Column<TimeSpan>(nullable: false),
            //         End = table.Column<TimeSpan>(nullable: false),
            //         Name = table.Column<string>(maxLength: 45, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true),
            //         AvailableTime = table.Column<TimeSpan>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Shift", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "STBLOnHandBuildReports",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         PartName = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Site = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         SourceType = table.Column<string>(nullable: true),
            //         Source = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Cell = table.Column<string>(nullable: true),
            //         OrderType = table.Column<string>(nullable: true),
            //         Status = table.Column<string>(nullable: true),
            //         DemandPlanSegment = table.Column<string>(nullable: true),
            //         OrderLine = table.Column<string>(nullable: true),
            //         CorporateBrand = table.Column<string>(nullable: true),
            //         RequestDate = table.Column<DateTime>(nullable: false),
            //         ShortCompCount = table.Column<int>(nullable: false),
            //         Hold = table.Column<string>(nullable: false),
            //         Quantity = table.Column<decimal>(nullable: false),
            //         UnitSellingPrice = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         ExtValue = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         FGOnHandQty = table.Column<decimal>(nullable: false),
            //         OnHandBuildQty = table.Column<int>(nullable: false),
            //         QtyOnWorngOrg = table.Column<int>(nullable: false),
            //         TotalBuildQuantity = table.Column<decimal>(nullable: false),
            //         STBLQtyInpanct = table.Column<int>(nullable: false),
            //         NetOH = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         RoutCauses = table.Column<string>(nullable: true),
            //         Notes = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         Component = table.Column<string>(nullable: true),
            //         ComponentDueDate = table.Column<DateTime>(nullable: false),
            //         Category = table.Column<string>(nullable: true),
            //         Module = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_STBLOnHandBuildReports", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "STBLTrends",
            //     columns: table => new
            //     {
            //         Date = table.Column<DateTime>(nullable: false),
            //         MFG = table.Column<int>(nullable: false),
            //         PFG = table.Column<int>(nullable: false),
            //         Total = table.Column<int>(nullable: false),
            //         Target = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_STBLTrends", x => x.Date);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "SupplyDemands",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         Type = table.Column<string>(nullable: true),
            //         Site = table.Column<string>(nullable: true),
            //         Cell = table.Column<string>(nullable: true),
            //         Buyer = table.Column<string>(nullable: true),
            //         Supplier = table.Column<string>(nullable: true),
            //         ABC = table.Column<string>(nullable: true),
            //         LeadTime = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         LTDate = table.Column<DateTime>(nullable: false),
            //         ShortageDate = table.Column<DateTime>(nullable: false),
            //         StdUnitCost = table.Column<decimal>(nullable: false),
            //         SafetyStockQty = table.Column<decimal>(nullable: false),
            //         OnHand = table.Column<decimal>(nullable: false),
            //         OpenPOs = table.Column<decimal>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_SupplyDemands", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Taxonomies",
            //     columns: table => new
            //     {
            //         ProductNumber = table.Column<string>(nullable: false),
            //         ProductName = table.Column<string>(nullable: true),
            //         PurchaseClass = table.Column<string>(nullable: true),
            //         PurchaseCategory = table.Column<string>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Taxonomies", x => x.ProductNumber);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "UM",
            //     columns: table => new
            //     {
            //         Code = table.Column<string>(maxLength: 4, nullable: false),
            //         Name = table.Column<string>(maxLength: 45, nullable: false),
            //         Plural = table.Column<string>(maxLength: 50, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_UM", x => x.Code);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Users",
            //     columns: table => new
            //     {
            //         UserName = table.Column<string>(nullable: false),
            //         Email = table.Column<string>(nullable: true),
            //         DisplayName = table.Column<string>(nullable: true),
            //         isMapped = table.Column<bool>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Users", x => x.UserName);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "WarehouseGroup",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Name = table.Column<string>(maxLength: 25, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_WarehouseGroup", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "WarehouseType",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Name = table.Column<string>(maxLength: 25, nullable: false),
            //         Decription = table.Column<string>(maxLength: 250, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_WarehouseType", x => x.Id);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Assortments",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         BinId = table.Column<int>(nullable: false),
            //         ConsumedDate = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         ConsumedEmp = table.Column<int>(nullable: false),
            //         AssortmentDate = table.Column<DateTime>(nullable: false),
            //         AssortmentEmp = table.Column<int>(nullable: false),
            //         Completed = table.Column<DateTime>(nullable: false),
            //         CompletedEmp = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Assortments", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Assortments_Bins_BinId",
            //             column: x => x.BinId,
            //             principalTable: "Bins",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "DJOLog",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Value1 = table.Column<string>(nullable: true),
            //         Value2 = table.Column<string>(nullable: true),
            //         Value3 = table.Column<string>(nullable: true),
            //         Date = table.Column<DateTime>(nullable: false),
            //         User = table.Column<string>(nullable: true),
            //         TypeId = table.Column<int>(nullable: true),
            //         Comment = table.Column<string>(nullable: true),
            //         IncomingPriorityId = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_DJOLog", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_DJOLog_IncomingPriorities_IncomingPriorityId",
            //             column: x => x.IncomingPriorityId,
            //             principalTable: "IncomingPriorities",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_DJOLog_DJOLogTypes_TypeId",
            //             column: x => x.TypeId,
            //             principalTable: "DJOLogTypes",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "ScorePerformances",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Date = table.Column<DateTime>(nullable: false),
            //         Performance = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         Score = table.Column<decimal>(nullable: false),
            //         ScoreCardId = table.Column<int>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_ScorePerformances", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_ScorePerformances_ScoreCards_ScoreCardId",
            //             column: x => x.ScoreCardId,
            //             principalTable: "ScoreCards",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "BreaksGroups",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         ShiftId = table.Column<int>(nullable: false),
            //         Name = table.Column<string>(maxLength: 45, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_BreaksGroups", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_BreaksGroups_Shift_ShiftId",
            //             column: x => x.ShiftId,
            //             principalTable: "Shift",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "ProjectedDates",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Date = table.Column<DateTime>(nullable: false),
            //         Type = table.Column<string>(nullable: true),
            //         Qty = table.Column<decimal>(type: "decimal(16,4)", nullable: false),
            //         SupplyDemandId = table.Column<int>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_ProjectedDates", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_ProjectedDates_SupplyDemands_SupplyDemandId",
            //             column: x => x.SupplyDemandId,
            //             principalTable: "SupplyDemands",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Claims",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         UserUserName = table.Column<string>(nullable: true),
            //         InternoRole = table.Column<int>(nullable: false),
            //         Claim = table.Column<string>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Claims", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Claims_Users_UserUserName",
            //             column: x => x.UserUserName,
            //             principalTable: "Users",
            //             principalColumn: "UserName",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Warehouse",
            //     columns: table => new
            //     {
            //         Code = table.Column<string>(maxLength: 13, nullable: false),
            //         Name = table.Column<string>(maxLength: 100, nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true),
            //         TypeId = table.Column<int>(nullable: false),
            //         Capacity = table.Column<float>(nullable: false),
            //         UnitCode = table.Column<string>(maxLength: 4, nullable: true),
            //         GroupId = table.Column<int>(nullable: true),
            //         Created = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Updated = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
            //         DeleteDate = table.Column<DateTime>(nullable: false),
            //         Delete = table.Column<bool>(nullable: false),
            //         Active = table.Column<bool>(nullable: false),
            //         Discriminator = table.Column<string>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Warehouse", x => x.Code);
            //         table.ForeignKey(
            //             name: "FK_Warehouse_WarehouseGroup_GroupId",
            //             column: x => x.GroupId,
            //             principalTable: "WarehouseGroup",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_Warehouse_WarehouseType_TypeId",
            //             column: x => x.TypeId,
            //             principalTable: "WarehouseType",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_Warehouse_UM_UnitCode",
            //             column: x => x.UnitCode,
            //             principalTable: "UM",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Break",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Code = table.Column<string>(maxLength: 15, nullable: false),
            //         Start = table.Column<TimeSpan>(nullable: false),
            //         End = table.Column<TimeSpan>(nullable: false),
            //         TypeId = table.Column<int>(nullable: true),
            //         Duration = table.Column<TimeSpan>(nullable: false),
            //         BreaksGroupId = table.Column<int>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Break", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Break_BreaksGroups_BreaksGroupId",
            //             column: x => x.BreaksGroupId,
            //             principalTable: "BreaksGroups",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_Break_BreakType_TypeId",
            //             column: x => x.TypeId,
            //             principalTable: "BreakType",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "OperationTime",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Guid = table.Column<Guid>(nullable: false),
            //         Keying = table.Column<int>(nullable: false),
            //         Product = table.Column<string>(nullable: false),
            //         Description = table.Column<string>(nullable: false),
            //         WarehouseCode = table.Column<string>(nullable: true),
            //         Operation = table.Column<string>(nullable: false),
            //         Operators = table.Column<int>(nullable: false),
            //         WorkControl = table.Column<string>(maxLength: 100, nullable: true),
            //         RunTime = table.Column<TimeSpan>(nullable: false),
            //         SetTime = table.Column<TimeSpan>(nullable: false),
            //         Hours = table.Column<double>(nullable: false),
            //         LMPU = table.Column<double>(nullable: false),
            //         Inprovement = table.Column<double>(nullable: false),
            //         OffSet = table.Column<decimal>(nullable: false),
            //         Repeat = table.Column<int>(nullable: false),
            //         Cost = table.Column<decimal>(nullable: false),
            //         Created = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Username = table.Column<string>(maxLength: 100, nullable: true),
            //         RoutId = table.Column<int>(nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_OperationTime", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_OperationTime_Rout_RoutId",
            //             column: x => x.RoutId,
            //             principalTable: "Rout",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_OperationTime_Warehouse_WarehouseCode",
            //             column: x => x.WarehouseCode,
            //             principalTable: "Warehouse",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Results",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Priority = table.Column<int>(nullable: false),
            //         Date = table.Column<DateTime>(nullable: false),
            //         ResourceCode = table.Column<string>(nullable: false),
            //         SubResourceCode = table.Column<string>(nullable: true),
            //         ShiftId = table.Column<int>(nullable: false),
            //         BreaksId = table.Column<int>(nullable: true),
            //         Operators = table.Column<int>(nullable: false),
            //         LeadTime = table.Column<TimeSpan>(nullable: false),
            //         InitialTime = table.Column<DateTime>(nullable: false),
            //         ScheduledStops = table.Column<TimeSpan>(nullable: false),
            //         ProductiveTime = table.Column<TimeSpan>(nullable: false),
            //         ScheduledOperatingTime = table.Column<TimeSpan>(nullable: false),
            //         OperativeTime = table.Column<TimeSpan>(nullable: false),
            //         OverTimeEnd = table.Column<DateTime>(nullable: false),
            //         OverTime = table.Column<TimeSpan>(nullable: false),
            //         PlanedTime = table.Column<TimeSpan>(nullable: false),
            //         Item = table.Column<string>(nullable: true),
            //         Description = table.Column<string>(nullable: true),
            //         WorkOrder = table.Column<string>(nullable: true),
            //         OrderQty = table.Column<int>(nullable: false),
            //         PlanQty = table.Column<int>(nullable: false),
            //         Actual = table.Column<int>(nullable: false),
            //         Rate = table.Column<double>(nullable: false),
            //         OEE = table.Column<double>(nullable: false),
            //         OE = table.Column<double>(nullable: false),
            //         TEP = table.Column<double>(nullable: false),
            //         Availability = table.Column<double>(nullable: false),
            //         Eficiency = table.Column<double>(nullable: false),
            //         FirstPassYield = table.Column<double>(nullable: false),
            //         OEE1 = table.Column<double>(nullable: false),
            //         TakTime = table.Column<TimeSpan>(nullable: false),
            //         Capacity = table.Column<double>(nullable: false),
            //         LMPU = table.Column<double>(nullable: false),
            //         Inprovement = table.Column<double>(nullable: false),
            //         ShippingDate = table.Column<DateTime>(nullable: false),
            //         WHSDate = table.Column<DateTime>(nullable: false),
            //         SMKTDate = table.Column<DateTime>(nullable: false),
            //         Date1 = table.Column<DateTime>(nullable: false),
            //         Date2 = table.Column<DateTime>(nullable: false),
            //         LeaderNumber = table.Column<int>(nullable: false),
            //         SupervisorNumber = table.Column<int>(nullable: false),
            //         Planner = table.Column<string>(nullable: true),
            //         Created = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Updated = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Results", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Results_BreaksGroups_BreaksId",
            //             column: x => x.BreaksId,
            //             principalTable: "BreaksGroups",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_Results_Warehouse_ResourceCode",
            //             column: x => x.ResourceCode,
            //             principalTable: "Warehouse",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_Results_Shift_ShiftId",
            //             column: x => x.ShiftId,
            //             principalTable: "Shift",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_Results_Warehouse_SubResourceCode",
            //             column: x => x.SubResourceCode,
            //             principalTable: "Warehouse",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "ShifGroupBrakes",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         ShiftId = table.Column<int>(nullable: false),
            //         BreakGroupId = table.Column<int>(nullable: false),
            //         BreakId = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_ShifGroupBrakes", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_ShifGroupBrakes_BreaksGroups_BreakGroupId",
            //             column: x => x.BreakGroupId,
            //             principalTable: "BreaksGroups",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_ShifGroupBrakes_Break_BreakId",
            //             column: x => x.BreakId,
            //             principalTable: "Break",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_ShifGroupBrakes_Shift_ShiftId",
            //             column: x => x.ShiftId,
            //             principalTable: "Shift",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "WorkOrders",
            //     columns: table => new
            //     {
            //         Id = table.Column<string>(nullable: false),
            //         Guid = table.Column<Guid>(nullable: false),
            //         Type = table.Column<int>(nullable: false),
            //         FinishItemCode = table.Column<string>(nullable: false),
            //         OperationTimeId1 = table.Column<int>(nullable: true),
            //         Alias = table.Column<string>(maxLength: 45, nullable: true),
            //         UMCode = table.Column<string>(maxLength: 4, nullable: true),
            //         OrderQty = table.Column<int>(nullable: false),
            //         ManufQty = table.Column<int>(nullable: false),
            //         Count = table.Column<int>(nullable: false),
            //         Status = table.Column<int>(nullable: false),
            //         MaterialStatus = table.Column<int>(nullable: false),
            //         Review = table.Column<string>(maxLength: 5, nullable: true),
            //         Lot = table.Column<long>(nullable: false),
            //         Cost = table.Column<double>(nullable: false),
            //         Release = table.Column<DateTime>(nullable: false),
            //         Request = table.Column<DateTime>(nullable: false),
            //         Start = table.Column<DateTime>(nullable: false),
            //         Finish = table.Column<DateTime>(nullable: false),
            //         Trascurred = table.Column<TimeSpan>(nullable: false),
            //         Downtime = table.Column<TimeSpan>(nullable: false),
            //         EstimatedTime = table.Column<TimeSpan>(nullable: false),
            //         EstimatedCost = table.Column<double>(nullable: false),
            //         Approved = table.Column<bool>(nullable: false),
            //         Responsible = table.Column<string>(maxLength: 100, nullable: true),
            //         Target = table.Column<string>(maxLength: 100, nullable: true),
            //         Planner = table.Column<string>(maxLength: 100, nullable: true),
            //         Comment = table.Column<string>(maxLength: 250, nullable: true),
            //         CustomerId1 = table.Column<int>(nullable: true),
            //         Affected = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn),
            //         RoutId1 = table.Column<int>(nullable: true),
            //         Class = table.Column<string>(maxLength: 100, nullable: true)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_WorkOrders", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_WorkOrders_Partnership_CustomerId1",
            //             column: x => x.CustomerId1,
            //             principalTable: "Partnership",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_WorkOrders_OperationTime_OperationTimeId1",
            //             column: x => x.OperationTimeId1,
            //             principalTable: "OperationTime",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_WorkOrders_Rout_RoutId1",
            //             column: x => x.RoutId1,
            //             principalTable: "Rout",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_WorkOrders_UM_UMCode",
            //             column: x => x.UMCode,
            //             principalTable: "UM",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Restrict);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Downtimes",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Guid = table.Column<Guid>(nullable: false),
            //         IssueId = table.Column<int>(nullable: false),
            //         ResultId = table.Column<int>(nullable: false),
            //         RequestNumber = table.Column<int>(nullable: false),
            //         Description = table.Column<string>(maxLength: 250, nullable: true),
            //         Status = table.Column<int>(nullable: false),
            //         AssignToNumber = table.Column<int>(nullable: false),
            //         Action = table.Column<string>(maxLength: 250, nullable: true),
            //         CommitDate = table.Column<DateTime>(nullable: false),
            //         ClosedDate = table.Column<DateTime>(nullable: false),
            //         Escalation = table.Column<DateTime>(nullable: false),
            //         Created = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Updated = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.ComputedColumn)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Downtimes", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Downtimes_Issues_IssueId",
            //             column: x => x.IssueId,
            //             principalTable: "Issues",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //         table.ForeignKey(
            //             name: "FK_Downtimes_Results_ResultId",
            //             column: x => x.ResultId,
            //             principalTable: "Results",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "EfficiencyHrs",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Date = table.Column<DateTime>(nullable: false),
            //         ResultId = table.Column<int>(nullable: false),
            //         ResourceCode = table.Column<string>(nullable: true),
            //         Item = table.Column<string>(nullable: true),
            //         StdTime = table.Column<double>(nullable: false),
            //         Meta = table.Column<int>(nullable: false),
            //         Pieces = table.Column<int>(nullable: false),
            //         EmployeesQty = table.Column<int>(nullable: false),
            //         PaidHrs = table.Column<double>(nullable: false),
            //         Issues = table.Column<int>(nullable: false),
            //         Downtime = table.Column<DateTime>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_EfficiencyHrs", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_EfficiencyHrs_Warehouse_ResourceCode",
            //             column: x => x.ResourceCode,
            //             principalTable: "Warehouse",
            //             principalColumn: "Code",
            //             onDelete: ReferentialAction.Restrict);
            //         table.ForeignKey(
            //             name: "FK_EfficiencyHrs_Results_ResultId",
            //             column: x => x.ResultId,
            //             principalTable: "Results",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "HourByHour",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         Hour = table.Column<DateTime>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         ResultId = table.Column<int>(nullable: false),
            //         ResourceCode = table.Column<string>(nullable: false),
            //         Meta = table.Column<int>(nullable: false),
            //         Pieces = table.Column<int>(nullable: false),
            //         Downtime = table.Column<DateTime>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_HourByHour", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_HourByHour_Results_ResultId",
            //             column: x => x.ResultId,
            //             principalTable: "Results",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateTable(
            //     name: "Labors",
            //     columns: table => new
            //     {
            //         Id = table.Column<int>(nullable: false)
            //             .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
            //         EmployeeNumber = table.Column<int>(nullable: false),
            //         ResourceCode = table.Column<string>(nullable: true),
            //         Start = table.Column<DateTime>(nullable: false),
            //         End = table.Column<DateTime>(nullable: false),
            //         TypeId = table.Column<int>(nullable: false),
            //         ResultId = table.Column<int>(nullable: false)
            //     },
            //     constraints: table =>
            //     {
            //         table.PrimaryKey("PK_Labors", x => x.Id);
            //         table.ForeignKey(
            //             name: "FK_Labors_Results_ResultId",
            //             column: x => x.ResultId,
            //             principalTable: "Results",
            //             principalColumn: "Id",
            //             onDelete: ReferentialAction.Cascade);
            //     });

            // migrationBuilder.CreateIndex(
            //     name: "IX_Assortments_BinId",
            //     table: "Assortments",
            //     column: "BinId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Break_BreaksGroupId",
            //     table: "Break",
            //     column: "BreaksGroupId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Break_TypeId",
            //     table: "Break",
            //     column: "TypeId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_BreaksGroups_ShiftId",
            //     table: "BreaksGroups",
            //     column: "ShiftId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Claims_UserUserName",
            //     table: "Claims",
            //     column: "UserUserName");

            // migrationBuilder.CreateIndex(
            //     name: "IX_DJOLog_IncomingPriorityId",
            //     table: "DJOLog",
            //     column: "IncomingPriorityId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_DJOLog_TypeId",
            //     table: "DJOLog",
            //     column: "TypeId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Downtimes_IssueId",
            //     table: "Downtimes",
            //     column: "IssueId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Downtimes_ResultId",
            //     table: "Downtimes",
            //     column: "ResultId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_EfficiencyHrs_ResourceCode",
            //     table: "EfficiencyHrs",
            //     column: "ResourceCode");

            // migrationBuilder.CreateIndex(
            //     name: "IX_EfficiencyHrs_ResultId",
            //     table: "EfficiencyHrs",
            //     column: "ResultId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_HourByHour_ResultId",
            //     table: "HourByHour",
            //     column: "ResultId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Labors_ResultId",
            //     table: "Labors",
            //     column: "ResultId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_OperationTime_RoutId",
            //     table: "OperationTime",
            //     column: "RoutId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_OperationTime_WarehouseCode",
            //     table: "OperationTime",
            //     column: "WarehouseCode");

            // migrationBuilder.CreateIndex(
            //     name: "IX_ProjectedDates_SupplyDemandId",
            //     table: "ProjectedDates",
            //     column: "SupplyDemandId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Results_BreaksId",
            //     table: "Results",
            //     column: "BreaksId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Results_ResourceCode",
            //     table: "Results",
            //     column: "ResourceCode");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Results_ShiftId",
            //     table: "Results",
            //     column: "ShiftId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Results_SubResourceCode",
            //     table: "Results",
            //     column: "SubResourceCode");

            // migrationBuilder.CreateIndex(
            //     name: "IX_ScorePerformances_ScoreCardId",
            //     table: "ScorePerformances",
            //     column: "ScoreCardId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_ShifGroupBrakes_BreakGroupId",
            //     table: "ShifGroupBrakes",
            //     column: "BreakGroupId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_ShifGroupBrakes_BreakId",
            //     table: "ShifGroupBrakes",
            //     column: "BreakId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_ShifGroupBrakes_ShiftId",
            //     table: "ShifGroupBrakes",
            //     column: "ShiftId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Warehouse_GroupId",
            //     table: "Warehouse",
            //     column: "GroupId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Warehouse_TypeId",
            //     table: "Warehouse",
            //     column: "TypeId");

            // migrationBuilder.CreateIndex(
            //     name: "IX_Warehouse_UnitCode",
            //     table: "Warehouse",
            //     column: "UnitCode");

            // migrationBuilder.CreateIndex(
            //     name: "IX_WorkOrders_CustomerId1",
            //     table: "WorkOrders",
            //     column: "CustomerId1");

            // migrationBuilder.CreateIndex(
            //     name: "IX_WorkOrders_OperationTimeId1",
            //     table: "WorkOrders",
            //     column: "OperationTimeId1");

            // migrationBuilder.CreateIndex(
            //     name: "IX_WorkOrders_RoutId1",
            //     table: "WorkOrders",
            //     column: "RoutId1");

            // migrationBuilder.CreateIndex(
            //     name: "IX_WorkOrders_UMCode",
            //     table: "WorkOrders",
            //     column: "UMCode");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Assortments");

            migrationBuilder.DropTable(
                name: "BackOrders");

            migrationBuilder.DropTable(
                name: "BalanceOnHands");

            migrationBuilder.DropTable(
                name: "BlankPOs");

            migrationBuilder.DropTable(
                name: "BOMs");

            migrationBuilder.DropTable(
                name: "BuyerKits");

            migrationBuilder.DropTable(
                name: "Claims");

            migrationBuilder.DropTable(
                name: "Completions");

            migrationBuilder.DropTable(
                name: "DJOLog");

            migrationBuilder.DropTable(
                name: "Downtimes");

            migrationBuilder.DropTable(
                name: "EfficiencyHrs");

            migrationBuilder.DropTable(
                name: "Goals");

            migrationBuilder.DropTable(
                name: "HourByHour");

            migrationBuilder.DropTable(
                name: "ItemPrices");

            migrationBuilder.DropTable(
                name: "Labors");

            migrationBuilder.DropTable(
                name: "Machines");

            migrationBuilder.DropTable(
                name: "MoveOrders");

            migrationBuilder.DropTable(
                name: "OpenSummaryReports");

            migrationBuilder.DropTable(
                name: "OTDReceipts");

            migrationBuilder.DropTable(
                name: "PlannedPOs");

            migrationBuilder.DropTable(
                name: "ProjectedDates");

            migrationBuilder.DropTable(
                name: "PurchaseOrders");

            migrationBuilder.DropTable(
                name: "PurchaseReceipts");

            migrationBuilder.DropTable(
                name: "Quotations");

            migrationBuilder.DropTable(
                name: "ScorePerformances");

            migrationBuilder.DropTable(
                name: "ShifGroupBrakes");

            migrationBuilder.DropTable(
                name: "STBLOnHandBuildReports");

            migrationBuilder.DropTable(
                name: "STBLTrends");

            migrationBuilder.DropTable(
                name: "Taxonomies");

            migrationBuilder.DropTable(
                name: "WorkOrders");

            migrationBuilder.DropTable(
                name: "Bins");

            migrationBuilder.DropTable(
                name: "Users");

            migrationBuilder.DropTable(
                name: "IncomingPriorities");

            migrationBuilder.DropTable(
                name: "DJOLogTypes");

            migrationBuilder.DropTable(
                name: "Issues");

            migrationBuilder.DropTable(
                name: "Results");

            migrationBuilder.DropTable(
                name: "SupplyDemands");

            migrationBuilder.DropTable(
                name: "ScoreCards");

            migrationBuilder.DropTable(
                name: "Break");

            migrationBuilder.DropTable(
                name: "Partnership");

            migrationBuilder.DropTable(
                name: "OperationTime");

            migrationBuilder.DropTable(
                name: "BreaksGroups");

            migrationBuilder.DropTable(
                name: "BreakType");

            migrationBuilder.DropTable(
                name: "Rout");

            migrationBuilder.DropTable(
                name: "Warehouse");

            migrationBuilder.DropTable(
                name: "Shift");

            migrationBuilder.DropTable(
                name: "WarehouseGroup");

            migrationBuilder.DropTable(
                name: "WarehouseType");

            migrationBuilder.DropTable(
                name: "UM");
        }
    }
}
