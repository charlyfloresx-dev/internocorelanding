using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.HumanResource.Models.Catalog
{
    public class Autority
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
    }
}
/*
    '7', 'Asisstant', 'A leader person and should represent themselves and their company well by acting as a role model to the people reporting to them.'
    '6', 'Employee', 'A person employed for wages or salary, especially at nonexecutive level'
    '5', 'Technical', 'A person skills against, talent and experience to perform a job or task .'
    '4', 'Especialist', 'A person who concentrates primarily on a particular subject or activity; a person highly skilled in a specific and restricted field.'
    '3', 'Supervisor', 'A person who supervises a person or an activity..'
    '2', 'Manager', 'A person responsible for controlling or administering all or part of a company or similar organization.'
    '1', 'Director', 'A person who is in charge of an activity, department, or organization.'
 */