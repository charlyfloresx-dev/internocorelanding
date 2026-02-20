using System;
using System.Linq;

namespace Interno.DJO.Data
{
    public static class DbInitilizer
    {
        public static void Initializer(Interno.DJO.DJOContext context)
        {
            
            if(!context.UM.Any())
            {
                var um = new Interno.Domain.Catalog.UM[]
                    {
                    
                    new Interno.Domain.Catalog.UM {Code= "EA", Name ="Each"},
                    new Interno.Domain.Catalog.UM {Code= "SF", Name ="Square feet"},
                    new Interno.Domain.Catalog.UM {Code= "YD", Name ="Yard"},
                    new Interno.Domain.Catalog.UM {Code= "LB", Name ="Pound"},
                    new Interno.Domain.Catalog.UM {Code= "GA", Name ="Gallon"},
                    new Interno.Domain.Catalog.UM {Code= "FT", Name ="Feet"},
                    new Interno.Domain.Catalog.UM {Code= "RL", Name ="Roll"},
                    new Interno.Domain.Catalog.UM {Code= "MT", Name ="Metre"},
                    new Interno.Domain.Catalog.UM {Code= "SM", Name ="Square metre"},
                    new Interno.Domain.Catalog.UM {Code= "SH", Name ="Sheet"},
                    new Interno.Domain.Catalog.UM {Code= "PK", Name ="Package"},
                    new Interno.Domain.Catalog.UM {Code= "SI", Name ="Square inches"},
                    new Interno.Domain.Catalog.UM {Code= "IN", Name ="Inches"},
                    new Interno.Domain.Catalog.UM {Code= "LT", Name ="Liter"},
                    new Interno.Domain.Catalog.UM {Code= "OZ", Name ="Ounce"}
                    
                };
                foreach (Interno.Domain.Catalog.UM u in um) context.UM.Add(u); 
            }
            
            if(!context.Partnership.Any())
            {
                Interno.Inventory.Models.Partnership par = new Interno.Inventory.Models.Partnership{ Code="GENERAL",Name="General Customer" };
                context.Partnership.Add(par);
            }
            if(!context.Shift.Any()){
                Interno.HumanResource.Models.Catalog.Shift shift = new HumanResource.Models.Catalog.Shift{ Code="T1",Start = TimeSpan.Parse("06:00"),End = TimeSpan.Parse("18:00"),Name="Primer Turno"};
                context.Shift.Add(shift);
                Interno.HumanResource.Models.Catalog.Shift shift2 = new HumanResource.Models.Catalog.Shift{ Code="T2",Start = TimeSpan.Parse("18:00"),End = TimeSpan.Parse("06:00"),Name="Segundo Turno" };
                context.Shift.Add(shift2);
            }
            
            
            
            if(!context.Break.Any())
            {
                if(!context.BreakType.Any()){
                    Interno.HumanResource.Models.Catalog.BreakType tipo = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Desayuno" };
                    context.Add(tipo);
                    Interno.HumanResource.Models.Catalog.BreakType tipo1 = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Comida" };
                    context.Add(tipo1);
                    Interno.HumanResource.Models.Catalog.BreakType tipo2 = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Descanso" };
                    context.Add(tipo2);

                    //Desallunos
                    var init = TimeSpan.Parse("7:30");
                    var end = TimeSpan.Parse("7:55");
                    for (int i = 1; i < 6; i++)
                    {
                        Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "D1"+i,Start = init,End = end, Duration = init- end,Type=tipo };
                        context.Add(break1);
                        init += TimeSpan.Parse("00:30:00");
                        end += TimeSpan.Parse("00:30:00");
                        Console.WriteLine(init); Console.WriteLine(end);
                    }
                    //Comidas
                    var init2 = TimeSpan.Parse("11:25");
                    var end2 = TimeSpan.Parse("11:50");
                    for (int i = 1; i < 5; i++)
                    {
                        Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "C1"+i,Start = init2,End = end2, Duration = init2- end2,Type=tipo1 };
                        context.Add(break1);
                        init2 += TimeSpan.Parse("00:30:00");
                        end2 += TimeSpan.Parse("00:30:00");
                        Console.WriteLine(init); Console.WriteLine(end);
                    }
                    //Descanzo 2
                    var init3 = TimeSpan.Parse("14:55");
                    var end3 = TimeSpan.Parse("15:05");
                    for (int i = 1; i < 5; i++)
                    {
                        Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "D2"+i,Start = init3,End = end3, Duration = init3- end3,Type=tipo2 };
                        context.Add(break1);
                        init2 += TimeSpan.Parse("00:15:00");
                        end2 += TimeSpan.Parse("00:15:00");
                        Console.WriteLine(init); Console.WriteLine(end);
                    }
                }
                
            }
            if(!context.Resources.Any())
            {
                Inventory.Models.WarehouseType type = new Inventory.Models.WarehouseType{ Name = "Module"};
                context.WarehouseType.Add(type);
                Interno.Production.Models.Resource[] res = {
                    new Interno.Production.Models.Resource{ Code = "M-01", Name = "Module 1", Type = type, BreakGroupId = 1 },
                    new Interno.Production.Models.Resource{ Code = "M-02", Name = "Module 2", Type = type, BreakGroupId = 1 },
                    new Interno.Production.Models.Resource{ Code = "M-03", Name = "Module 3", Type = type, BreakGroupId = 1 }
                };
                foreach (var item in res) context.Resources.Add(item);
            }
            if(!context.Issues.Any())
            {
                Production.Models.ProdIssue[] issues = {
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Enfermería"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Baños"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Juntas"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Entrenamiento"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Inventarios"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Auditorias"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Personal, Description = "Recursos Humanos"},

                    // new Production.Models.Issue { Type = Production.Models.IssueType.Material, Description = "Falta de Insumos"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Material, Description = "Falta de Materia Prima"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Material, Description = "Materia Prima Defectuosa"},

                    // new Production.Models.Issue { Type = Production.Models.IssueType.Method, Description = "Prueba Piloto"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Method, Description = "Método Ineficiente"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Method, Description = "Método Inexistente"},

                    // new Production.Models.Issue { Type = Production.Models.IssueType.Equipment, Description = "Equipo Caido"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Equipment, Description = "Herramienta Defectuosa"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Equipment, Description = "Falta de Herramienta"},

                    // new Production.Models.Issue { Type = Production.Models.IssueType.Service, Description = "Intranet"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Service, Description = "Corriente Eléctrica"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Service, Description = "Aire Comprimido"},
                    // new Production.Models.Issue { Type = Production.Models.IssueType.Service, Description = "Programa de Computadora"},

                    // new Production.Models.Issue { Type = Production.Models.IssueType.Management, Description = "Sin Plan de Produccion"},
                };
                foreach (var item in issues) context.Issues.Add(item);
            }
            Console.WriteLine(context.SaveChanges());
        }
    }
}